#mdblog
import markdown as md
import os
import string
import datetime as dt
import json

gtags = dict()

class Article:
    def create(self,f):
        statr = os.stat(f)
        self.finfo = {'filename': f,'ctime': statr.st_ctime,'mtime': statr.st_mtime }
        with open(f,'rb') as fh:
            self.finfo['title'] = string.strip(fh.readline())
            self.finfo['tags'] = map(string.strip,fh.readline().split(','))
            self.addGlobalTags()
            if os.path.exists('cache/' + f + '.html'):
                #if cache'd file is older than raw then update it
                cstat = os.stat('cache/' + f + '.html')
                cmtime = dt.datetime.fromtimestamp(cstat.st_mtime)
                mtime = dt.datetime.fromtimestamp(statr.st_mtime)
                if mtime > cmtime:
                    with open('cache/' + f + '.html','wb') as ch:
                        ch.write(md.markdown(fh.read()))
            else:
                self.content = md.markdown(fh.read())
                if os.path.exists('cache') == False:
                    os.mkdir('cache')
                with open('cache/' + f + '.html','wb') as ch:
                    ch.write(self.content)

    def addGlobalTags(self):
        for t in self.finfo['tags']:
            if t in gtags:
                gtags[t].append(self.finfo['filename'])
            else:
                gtags[t] = [self.finfo['filename']]

    def createdTime(self):
        return self.finfo['ctime']

    def modifiedTime(self):
        return self.finfo['mtime']

    def title(self):
        return self.finfo['title']

def filterFiles(path):
    if( os.path.isfile(path)):
        f = os.path.splitext(path)
        if( len(f) == 2):
            if( f[1] == '.md'):
                return True
    return False

def getArticles():
    try:
        with open('config.json','rb') as fp:
            tcon = json.load(fp)
    except IOError:
        tcon = dict()
    flist = filter(filterFiles, os.listdir(os.curdir))
    articles = dict()
    for f in flist:
        articles[f] = Article()
        articles[f].create(f)
    return tcon, articles


