# removepdfwatermark

This is a small tool to remove image/link/text in a pdf file.

## How To Use

### Remove an image

1. First, you should find the size of image.
```bash
python removewatermark.py image -i xxx.pdf -o /tmp/
# this will export all the images in the pdf file to '/tmp/' directory, the filename will contains size of the image like 'pg_5_179x52_Im1.png' 
```
2. Second, check all the images to find size of the one you want to remove 
3. Specify the size of image, the tool will remove all the image with the same size. 

```bash
# use --remove-page if you want to remove the whole page if there is an image to remove.
python3.8 removewhitemark.py remove --verbose --image-size 179,52 -i xxx.pdf --remove-page
```

## Remove an link

```bash
# use --remove-page if you want to remove the whole page if there is an link to remove.
python3.8 removewhitemark.py remove --links 'http://guide.medlive.cn/'
```

## Remove text
```bash
# use --remove-page if you want to remove the whole page if there is text to remove.
python3.8 removewhitemark.py remove --pattern 'hello \\s\\+world'
```

## Remove image & link & text at the same time

```bash
python3.8 removewhitemark.py remove --verbose --image-size 179,52 --links 'http://guide.medlive.cn/' --pattern 'hello \\s\\+world' --remove-page  -i xxx.pdf 
```


