#!/usr/bin/env python3
"""
    Remove Link/Image/Text from pdf document.
    Based on pymupdf
"""
from pathlib import Path
import fitz
import logging
import re

class RemoveWatermark:
    def __init__(self, input_file: str):
        """
        Args:
            input_file (str): pdf file to remove watermark
        """
        self.input_file = input_file
        self.doc = fitz.open(input_file)

    def removeLink(self, url: str, remove_page=False):
        """remove link from document

        Args:
            url (str): url to remove
        """
        count = 0
        removed_pages = []
        for pn in range(0, self.doc.pageCount):
            page = self.doc[pn]
            lnks = page.getLinks()
            for lnk in lnks:
                page.apply_redactions()
                logging.info(lnk.get('uri'))
                if lnk.get('uri') == url:
                    if remove_page:
                        removed_pages.append(pn)
                        break
                    page.addRedactAnnot(lnk["from"])
                    page.deleteLink(lnk)
                    count += 1
        self.removePages(removed_pages)
        logging.info(f'{count} link is removed')
        return self

    def removePages(self, pages):
        if not pages:
            return
        keep_pages = []
        for i in range(0, self.doc.pageCount):
            if i not in pages:
                keep_pages.append(i)
        self.doc.select(keep_pages)

    def removeImage(self, width=0, height=0, name=None, remove_page=False):
        """Remove image from document by image size(width & height) or name
        Args:
            width (int, optional): image width. Defaults to 0.
            height (int, optional): image height. Defaults to 0.
            name (str, optional): image name. Defaults to None.
        """
        count = 0
        removed_pages = []
        for pn in range(0, self.doc.pageCount):
            page = self.doc[pn]
            logging.debug(f'Images in page {pn}:')
            for image in self.doc.getPageImageList(pn):
                logging.debug(image)
                image_name = image[7]
                if (image[2] == width and image[3] == height) or \
                    image_name == name:
                    if remove_page:
                        removed_pages.append(pn)
                        break
                    rect = page.getImageBbox(image_name)
                    page.addRedactAnnot(rect," ",fill=False)
                    page.apply_redactions()
                    count += 1
        self.removePages(removed_pages)
        logging.info(f'{count} image is removed')

    @staticmethod
    def getPattern(lines, pattern):
        for line in lines:
            m = pattern.search(line)
            if m:
                yield m.group(0)

    def removePattern(self, regex: str, remove_page=False):
        """remove text which matched the regex
        Args:
            regex (str): regex string
        """
        count = 0
        pattern = re.compile(regex)
        removed_pages = []
        pn = -1
        # iterating through pages
        for page in self.doc:
            pn += 1
            # _wrapContents is needed for fixing
            # alignment issues with rect boxes in some
            # cases where there is alignment issue
            page.wrapContents()
            # geting the rect boxes which consists the matching email regex
            matched_data = self.getPattern(page.getText("text")
                                                .split('\n'), pattern)
            for data in matched_data:
                if remove_page:
                    removed_pages.append(pn)
                    break
                areas = page.searchFor(data)
                for area in areas:
                    page.addRedactAnnot(area, " ", fill=False)
                    count += 1
            page.apply_redactions()
        self.removePages(removed_pages)
        logging.info(f'{count} item matched pattern is removed')
        return self

    def save(self, output_file):
        """save the modified document

        Args:
            output_file (str): file path
        """
        self.doc.save(output_file, garbage=3, deflate=True)

    def exportImage(self, output_path: str):
        """Export images in pdf document

        Args:
            output_path (Path): Directory to save images
        """
        out_dir = Path(output_path)
        out_dir.mkdir(parents=True, exist_ok=True)
        count = 0
        for pn in range(0, self.doc.pageCount):
            logging.debug(f'Images in page {pn}:')
            for image in self.doc.getPageImageList(pn):
                logging.debug(image)
                xref = image[0]
                image_path = out_dir.joinpath(f'pg_{pn}_{image[2]}x{image[3]}_{image[7]}.png')
                if not image_path.exists():
                    pix = fitz.Pixmap(self.doc, xref)
                    if pix.n - pix.alpha < 4: # this is GRAY or RGB or pix.n < 5
                        pix.writePNG(image_path.as_posix())
                    else: # CMYK: convert to RGB first
                        pix1 = fitz.Pixmap(fitz.csRGB, pix)
                        pix1.writePNG(image_path.as_posix())
                    count += 1
                    logging.info(f'{image_path.as_posix()} is saved')
                else:
                    logging.info('Duplicate image %s', image_path.as_posix())
        logging.info(f'{count} image is exported')


def getArgs():
    from argparse import ArgumentParser
    parser = ArgumentParser()
    sub_parsers = parser.add_subparsers(dest='action')
    remove_parser = sub_parsers.add_parser('remove', help='remove watermark')
    remove_parser.add_argument('-i', dest='input_file', required=False)
    remove_parser.add_argument('-o', dest='output_path', help='new file path, Default: input_path.new.pdf')
    remove_parser.add_argument('--links', dest='links', nargs='*', help='Urls to remove')
    remove_parser.add_argument('--image-size', nargs='*', dest='image_sizes', help='size of image to remove, Format: width1,height1 width2,height2')
    remove_parser.add_argument('--pattern', help='regex pattern to remove')
    remove_parser.add_argument('--remove-page', action='store_true', dest='remove_page', help='if there is a text or link or image matched, the whole page is removed')
    remove_parser.add_argument('-v', '--verbose', action='store_true')

    image_parser = sub_parsers.add_parser('image', help='extract all the images in pdf')
    image_parser.add_argument('-i', dest='input_file', required=True)
    image_parser.add_argument('-o', dest='output_path', default='images')
    return parser.parse_args()

def main():
    args = getArgs()
    if args.action == 'remove':
        if args.verbose:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.INFO)
        input_path = Path(args.input_file).resolve()
        if input_path.is_dir():
            file_list = input_path.glob("**/*.pdf")
        else:
            file_list = [input_path]

        if args.output_path:
            out_dir = Path(args.output_path)
            out_dir.mkdir(parents=True, exist_ok=True)
        else:
            out_dir = None

        for input_file in file_list:
            if not out_dir:
                # save to the same directory as input file if output_path is not specified
                output_file = input_file.parent.joinpath(input_file.stem + '_new.pdf')
            else:
                output_file = out_dir.joinpath(input_file.name)

            r = RemoveWatermark(str(input_file))
            if args.links:
                for link in args.links:
                    #r.removeLink('http://guide.medlive.cn/')
                    r.removeLink(link, remove_page=args.remove_page)
            if args.image_sizes:
                for item in args.image_sizes:
                    width, height = (int(s) for s in item.split(','))
                    r.removeImage(width=width, height=height, remove_page=args.remove_page)
                    #r.removeImage(width=480, height=201, save_image=args.save_image)
            if args.pattern:
                r.removePattern(args.pattern, args.remove_page)
            r.save(output_file)
    elif args.action == 'image':
        r = RemoveWatermark(args.input_file)
        r.exportImage(args.output_path)

if __name__ == '__main__':
    main()
