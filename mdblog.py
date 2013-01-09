#mdblog
import markdown as md
import os
import string
import datetime as dt
import json
import urllib
import re

gtags = dict()
articlelinks = dict()
gconfig = dict()
garticles = dict()

class Article:
    def create(self,f):
        statr = os.stat(f)
        self.finfo = {'filename': f,'ctime': statr.st_ctime,'mtime': statr.st_mtime }
        with open(f,'rb') as fh:
            self.finfo['title'] = string.strip(fh.readline())
            articlelinks[f] = urllib.quote(self.finfo['title']) + ".html"
            self.finfo['tags'] = map(string.strip,fh.readline().split(','))
            self.addGlobalTags()
            self.content = fh.read()

    def updateCache(self):
        f = self.finfo['filename']
        if os.path.exists('cache/' + f + '.html'):
            #if cache'd file is older than raw then update it
            cstat = os.stat('cache/' + f + '.html')
            cmtime = dt.datetime.fromtimestamp(cstat.st_mtime)
            mtime = dt.datetime.fromtimestamp(self.finfo['mtime'])
            if mtime > cmtime:
                with open('cache/' + f + '.html','wb') as ch:
                    self.content = md.markdown(self.content)
                    ch.write(self.content)
            else:
                with open('cache/' + f + '.html','rb') as ch:
                    self.content = ch.read()
        else:
            self.content = md.markdown(self.content)
            if os.path.exists('cache') == False:
                os.mkdir('cache')
                with open('cache/' + f + '.html','wb') as ch:
                    ch.write(self.content)


    def expandMacros(self):
        for m in gconfig['macros']:
            e = gconfig['macros'][m]
            self.content = string.replace(self.content,'{'+m+'}',e)
            tempx = self.content
        for lx in re.finditer('\{link:(?P<file>.*\.md)\}',tempx):
            lx_file = string.strip(lx.groups()[0]).encode('utf-8')
            lx_repl = lx.group(0)
            lx_html = '<a href="'+string.strip(articlelinks[lx_file])+'">'+garticles[lx_file].title()+'</a>'
            self.content = string.replace(tempx,lx_repl,lx_html)

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
    global gconfig
    global garticles
    try:
        with open('config.json','rb') as fp:
            gconfig = json.load(fp)
    except IOError:
        tcon = dict()
    flist = filter(filterFiles, os.listdir(os.curdir))
    for f in flist:
        garticles[f] = Article()
        garticles[f].create(f)
    for a in garticles:
        garticles[a].expandMacros()
        garticles[a].updateCache()
    return garticles

def processTags(art):
    xheader = ' <a href="categories.html#'
    xmid = '">'
    xend = '</a>'
    ret = ''
    for t in art.finfo['tags']:
        ret = ret + xheader + t + xmid + t + xend
    return ret

def prepareArticle(tout,art):
    xout = string.replace(tout,'{site_title}',gconfig['site_title'])
    xout = string.replace(xout,'{title}',art.title())
    xout = string.replace(xout,'{author}',gconfig['author'])
    xout = string.replace(xout,'{date}',dt.datetime.fromtimestamp(art.modifiedTime()).strftime(gconfig['date_format']))
    xout = string.replace(xout,'{tags}',processTags(art))
    #content replacement occurs last
    return string.replace(xout,'{article}',art.content)

def writeTags():
    with open('out/categories.html','wb') as wh:
        wh.write('<html><title>Categories | ' + gconfig['site_title'] + '</title><body>')
        for t in gtags:
            wh.write('<a name="'+t+'"><h3>'+t+'</h3></a><ul>')
            for f in gtags[t]:
                wh.write('<li><a href="'+articlelinks[f]+'">'+garticles[f].title()+'</a></li>')
            wh.write('</ul>')
        wh.write('</body></html>')

def archiveList(l):
    al = l
    al.sort(key= lambda c : c.finfo['ctime'])
    al.reverse()
    dlist = dict()
    for i in al:
        d = dt.datetime.fromtimestamp(i.createdTime())
        dyear = str(d.year)
        dmon = d.strftime("%B")
        if dlist.has_key(dyear) == False:
            dlist[dyear] = dict()
        if dlist[dyear].has_key(dmon) == False:
            dlist[dyear][dmon] = []
        dlist[dyear][dmon].append(i)
    return dlist

#TODO: make more generic so can be used to generate for specified timeframe
def makeArchive():
    al = archiveList(garticles.values())
    with open('out/archive.html','wb') as fh:
        fh.write('<html><head><title>Archive | ' + gconfig['site_title'] + '</title></head><body>')
        for y in al:
            fh.write('<h1>'+str(y)+'</h1>')
            for m in al[y]:
                fh.write("<h2>"+str(m)+'</h2>')
                for i in al[y][m]:
                    fh.write('<a href="'+articlelinks[i.finfo['filename']]+'">'+i.title()+'</a><br />')
        fh.write('</body></html>')

def main():
    c = getArticles()
    if os.path.exists('out') == False:
        os.mkdir('out')
    for f in c:
        art = c[f]
        with open(gconfig['template'],'rb') as rh:
            tout = rh.read()
        out = prepareArticle(tout,art)
        with open('out/'+urllib.unquote(articlelinks[f]),'wb') as fh:
            fh.write(out)
    writeTags()
    makeArchive()

#TODO: move articles to articles directory, templates etc...
#TODO: generate index page
if __name__ == '__main__':
    main()
