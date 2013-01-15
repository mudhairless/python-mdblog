#!/bin/env python
import string
import time
import os
import random
import datetime

ipsum = """
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed pharetra tortor sed risus ullamcorper fringilla. Nulla bibendum metus ac magna porttitor tristique. Maecenas consectetur, nulla ut auctor vehicula, nulla lacus dapibus orci, ut imperdiet quam sem vitae turpis. Vivamus felis tortor, fringilla id varius nec, rhoncus eget purus. Pellentesque adipiscing tempus felis, id volutpat risus consectetur feugiat. Nam in lacus arcu. Proin congue accumsan accumsan. Aliquam sem nulla, blandit nec molestie ac, gravida sit amet lorem. Etiam in nunc nisl. Proin non lectus eu nisl tempor placerat at eget diam. Vestibulum nec urna eu mauris dignissim adipiscing at eget diam. Nulla malesuada nibh viverra mauris rhoncus sollicitudin. Nulla auctor arcu et lacus placerat non eleifend dui faucibus. Curabitur tellus est, tristique quis lacinia non, pellentesque lacinia odio. Nulla aliquam commodo tempus.


"""
ipsum_t = set('Lorem ipsum dolor sit amet consectetur adipiscing elit Sed pharetra tortor sed risus ullamcorper fringilla Nulla bibendum metus ac magna porttitor tristique Maecenas consectetur nulla ut auctor vehicula nulla lacus dapibus orci ut imperdiet quam sem vitae turpis Vivamus felis tortor fringilla id varius nec rhoncus eget purus Pellentesque adipiscing tempus felis id volutpat risus consectetur feugiat Nam in lacus arcu Proin congue accumsan accumsan Aliquam sem nulla blandit nec molestie ac gravida sit amet lorem Etiam in nunc nisl Proin non lectus eu nisl tempor placerat at eget diam Vestibulum nec urna eu mauris dignissim adipiscing at eget diam Nulla malesuada nibh viverra mauris rhoncus sollicitudin Nulla auctor arcu et lacus placerat non eleifend dui faucibus Curabitur tellus est tristique quis lacinia non pellentesque lacinia odio Nulla aliquam commodo tempus'.lower().split())
ipsum_l = []
for x in ipsum_t:
    ipsum_l.append(x)

def writeIpsum(f):
    tcount = random.randrange(1,40)
    count = 0

    article_t = 'article ' + str(random.randrange(1,5000000)) + '\n'
    article_tags = ','.join(random.sample(ipsum_l,random.randrange(1,6))) + '\n'

    f.write(article_t)
    f.write(article_tags)

    while count < tcount:
        f.write(ipsum)
        count = count + 1

def genArticles(n):
    count = 0
    while count < n:
        afile = string.replace('articles/article{n}.md','{n}',str(count))
        with open(afile,'wb') as fp:
            writeIpsum(fp)
        filedate = datetime.datetime(random.randrange(2000,2012),random.randrange(1,12),random.randrange(1,28),random.randrange(1,24),random.randrange(1,60),random.randrange(1,60))
        fdts = time.mktime(filedate.timetuple())
        os.utime(afile,(fdts,fdts))
        count = count + 1

if __name__ == '__main__':
    #has been tested up to ~4800 articles, took ~1.5 minutes to write to disk, ~11 minutes to process
    articles = 100
    print('Generating ' + str(articles) + ' articles, may take some time...')
    genArticles(articles)
