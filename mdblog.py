#mdblog
import markdown as md
import os
import string

class Article:
    def load(self,d):
        self.finfo = d

    def create(self,f):
        statr = os.stat(f)
        self.finfo = {'filename': f,'ctime': statr.st_ctime,'mtime': statr.st_mtime }
        with open(f,'rb') as fh:
            self.finfo['title'] = string.strip(fh.readline())
            self.content = fh.read()

    def createdTime(self):
        return self.finfo['ctime']

    def modifiedTime():
        return self.finfo['mtime']

    def title(self):
        return self.finfo['title']



def convertMarkdownToHTML(f):
    fo = open(f,'r')
    text = fo.read()
    fo.close()
    return md.markdown(text)

def filterFiles(path):
    if( os.path.isfile(path)):
        f = os.path.splitext(path)
        if( len(f) == 2):
            if( f[1] == '.md'):
                return True
    return False


def getArticles():
    flist = filter(filterFiles, os.listdir(os.curdir))
    articles = dict()
    for f in flist:
        articles[f] = Article()
        articles[f].create(f)
    return flist, articles


