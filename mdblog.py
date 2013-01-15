#!/bin/env python
#    mdblog - static 'blog' site creator
#    Copyright (C) 2013 Ebben Feagan
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
#    The included 'basic' theme is hereby released into the public domain

import markdown as md
import os
import string
import datetime as dt
import json
import urllib
import re
import uuid

gtags = dict()
articlelinks = dict()
gconfig = dict()
garticles = dict()
gtemplate = dict()
gartids = dict()

default_about_file = """
{author-name} hasn't written their about page yet!
"""

default_config_file = """
{
"template": "basic",
"base-url": "http://sample.url.com",
"author": "Joe Blogger",
"date-format":"%c",
"index-count":5,
"index-teaser-length":2,
"link-name-about":true,
"site-title": "Adventures in blogging",
"pages": {
    "tags": "categories.html",
    "archive": "archive.html",
    "about": {
        "output": "about.html",
        "input":"about.md"
        }
    }
}
"""

default_template_file = """
{
    "article":"{tpage-head-start}{title} | {site-title}{tpage-head-end}{header}<h2>{title}</h2><div class=\"byline\"><p>Posted {date} by <em>{author}</em></p></div><div class=\"content\">{article}</div><div class=\"tags\"><p>Filed under: {tags}</p><p><a href=\"{permalink}\">Permalink</a></p></div>{footer}{html-end}",
    "taglist": {
        "base":"{tpage-head-start}{title} | {site-title}{tpage-head-end}{header}<h2>{title}</h2><div class=\"content\">{body}</div>{footer}{html-end}",
        "section-start":"<a name=\"{tag}\"><h3>{tag}</h3></a><div>",
        "list-header":"<ul>",
        "list-item":"<li><a href=\"{link}\">{link-title}</a></li>",
        "list-footer":"</ul>",
        "section-end":"</div>"
        },
    "index": {
        "base":"{tpage-head-start}{site-title}{tpage-head-end}{header}<h2>{site-slogan}</h2><div class=\"content\">{body}</div>{footer}{html-end}",
        "list-header":"<div class=\"entry-title\">",
        "list-item":"<h2><a href=\"{link}\">{post-title}</a></h2><div class=\"entry-teaser\">{post-teaser}</div>",
        "list-footer":"</div>",
        "links": {
            "archive":"<div class=\"pagelink\"><a href=\"{link}\">Archive</a></div>",
            "next-page":"<div class=\"pagelink\"><a href=\"{link}\">Newer Posts</a></div>",
            "prev-page":"<div class=\"pagelink\"><a href=\"{link}\">Older Posts</a></div>",
            "wrapper":"<div class=\"paginationlinks\"{prev-page}{archive}{next-page}</div>"
        }
    },
    "macros": {
        "site-slogan":"Experiencing Life, through code!",
        "header":"<div class=\"header\"><h1><a href=\"{page-index}\">{site-title}</a></h1></div>",
        "footer":"<div class=\"footer\">{copy}</div>",
        "copy":"Copyright &copy; {year} {author}",
        "tpage-head-start":"<html><head><title>",
        "tpage-head-end":"</title></head><body>",
        "html-end":"</body></html>"
    }
}
"""

class Article:
    def create(self,f):
        statr = os.stat(f)
        if f not in gartids:
            gartids[f] = str(uuid.uuid4())
        self.finfo = {'filename': f,'ctime': statr.st_atime,'mtime': statr.st_mtime }
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
        self.content = expandMacros(self.content)

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

def expandMacros(text):
    tempx = text
    for m in gconfig['macros']:
        e = gconfig['macros'][m]
        tempx = string.replace(tempx,'{'+m+'}',e)

    for lx in re.finditer('\{link:(?P<file>.*\.md)\}',tempx):
        lx_file = string.strip(lx.groups()[0]).encode('utf-8')
        lx_repl = lx.group(0)
        lx_html = '<a href="'+string.strip(articlelinks[lx_file])+'">'+garticles[lx_file].title()+'</a>'
        tempx = string.replace(tempx,lx_repl,lx_html)

    if re.search('\{*?\}',tempx) != None:
        if re.search('$$debug',tempx) != None:
            print(tempx)
        tempx = expandMacros(tempx)

    return tempx

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

    os.chdir('articles')
    flist = filter(filterFiles, os.listdir(os.curdir))
    for f in flist:
        garticles[f] = Article()
        garticles[f].create(f)
    os.chdir('..')
    for a in garticles:
        garticles[a].expandMacros()
        garticles[a].updateCache()
    return garticles

def processTags(art):
    xheader = ' <a href="'+gconfig['pages']['tags']+'#'
    xmid = '">'
    xend = '</a>'
    ret = ''
    for t in art.finfo['tags']:
        ret = ret + xheader + t + xmid + t + xend
    return ret

def prepareArticle(tout,art):
    xout = string.replace(tout,'{title}',art.title())
    xout = string.replace(xout,'{date}',dt.datetime.fromtimestamp(art.modifiedTime()).strftime(gconfig['date-format']))
    xout = string.replace(xout,'{tags}',processTags(art))
    #content replacement occurs last
    return string.replace(xout,'{article}',art.content)

def writeTags():
    output = ''
    listout = ''
    base = gtemplate['taglist']['base']
    anchor = gtemplate['taglist']['section-start']
    liststart = gtemplate['taglist']['list-header']
    listitem = gtemplate['taglist']['list-item']
    listend = gtemplate['taglist']['list-footer']
    endsection = gtemplate['taglist']['section-end']

    sorted_gtags = gtags.keys()
    sorted_gtags.sort()

    for t in sorted_gtags:
        tanchor = string.replace(anchor,'{tag}',t)
        listout = listout + tanchor + liststart
        for f in gtags[t]:
            tlistitem = string.replace(listitem,'{link}',articlelinks[f])
            tlistitem = string.replace(tlistitem,'{link-title}',garticles[f].title())
            listout = listout + tlistitem
        listout = listout + listend
        listout = listout + endsection
    output = string.replace(base,'{title}','Tag List')
    output = string.replace(output,'{body}',listout)
    output = string.replace(output,'{posted-date}','')
    output = expandMacros(output)
    with open('out/'+gconfig['pages']['tags'],'wb') as wh:
        wh.write(output)

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

def makeArchive():
    al = archiveList(garticles.values())
    out = string.replace(gtemplate['taglist']['base'],'{title}','Archive')
    body = ''
    al_keys = al.keys()
    al_keys.sort()
    al_keys.reverse()
    months = ['January','February','March','April','May','June','July','August','September','October','November','December']
    months.reverse()
    for y in al_keys:
        body = body + string.replace(gtemplate['taglist']['section-start'],'{tag}',str(y))
        for m in months:
            if al[y].has_key(m):
                body = body + string.replace(gtemplate['taglist']['section-start'],'{tag}',str(m))
                body = body + gtemplate['taglist']['list-header']
                for i in al[y][m]:
                    ida = dt.datetime.fromtimestamp(i.createdTime())
                    xbody = string.replace(gtemplate['taglist']['list-item'],'{link}',articlelinks[i.finfo['filename']])
                    body = body + string.replace(xbody,'{link-title}',i.title())
                    body = string.replace(body,'{posted-date}',ida.strftime(gconfig['date-format']))
                body = body + gtemplate['taglist']['list-footer']
        body = body + gtemplate['taglist']['section-end']
    out = string.replace(out,'{body}',body)
    out = expandMacros(out)
    with open('out/'+gconfig['pages']['archive'],'wb') as fh:
        fh.write(out)

def loadDefaults():
    global gconfig
    if gconfig.has_key("pages"):
        if gconfig['pages'].has_key('tags'):
            pass
        else:
            gconfig['pages']['tags'] = 'categories.html'
        if gconfig['pages'].has_key(''):
            pass
        else:
            gconfig['pages']['archive'] = 'archive.html'
        if gconfig['pages'].has_key('about'):
            if gconfig['pages']['about'].has_key('output'):
                pass
            else:
                gconfig['pages']['about']['output'] = 'about.html'
            if gconfig['pages']['about'].has_key('input'):
                pass
            else:
                gconfig['pages']['about']['input'] = 'about.md'
        else:
            gconfig['pages']['about'] = dict()
            gconfig['pages']['about']['output'] = 'about.html'
            gconfig['pages']['about']['input'] = 'about.md'
    else:
        gconfig['pages'] = dict()
        loadDefaults()

    d = dt.datetime.now()
    if gconfig.has_key('macros'):
        gconfig['macros']['year'] = d.strftime('%Y')
        gconfig['macros']['build-time'] = d.strftime(gconfig['date-format'])
        if gconfig.has_key('link-name-about') & gconfig['link-name-about'] == True:
            gconfig['macros']['author'] = '<a href="'+gconfig['pages']['about']['output']+'">'+gconfig['author']+'</a>'
        else:
            gconfig['macros']['author'] = gconfig['author']
        gconfig['macros']['author-name'] = gconfig['author']
        gconfig['macros']['base-href'] = gconfig['base-url']
        gconfig['macros']['site-title'] = gconfig['site-title']
        gconfig['macros']['page-index'] = 'index.html'
        gconfig['macros']['page-about'] = gconfig['pages']['about']['output']
        gconfig['macros']['page-tags'] = gconfig['pages']['tags']
        gconfig['macros']['page-archive'] = gconfig['pages']['archive']
    else:
        gconfig['macros'] = dict()
        if gtemplate.has_key('macros'):
            gconfig['macros'].update(gtemplate['macros'])
        loadDefaults()

def genAboutPage():
    page_content = ""
    with open(gconfig['pages']['about']['input'],'rb') as fp:
        page_content = md.markdown(fp.read())
    xout = string.replace(gtemplate['article'],'{article}',page_content)
    xout = string.replace(xout,'{title}','About ' + gconfig['author'])
    xout = string.replace(xout,'{date}',dt.datetime.now().strftime(gconfig['date-format']))
    xout = string.replace(xout,'{tags}','<em>About Page</em>')
    gconfig['macros']['page-id'] = 'About Page'
    gconfig['macros']['permalink'] = string.replace(gconfig['base-url'] + '/' + gconfig['pages']['about']['output'],' ','%20')
    xout = expandMacros(xout)
    gconfig['macros']['page-id'] = ''
    gconfig['macros']['permalink'] = ''
    with open('out/'+gconfig['pages']['about']['output'],'wb') as fp:
        fp.write(xout)

def buildTeaser(t):
    l = t.split("</p>")
    pc = gconfig['index-teaser-length'] - 1
    out = ''
    if pc > len(l):
        pc = len(l) - 1
    if pc < 0:
        pc = 0
    count = 0
    while count <= pc:
        out = out + l[count] + '</p>'
        count = count + 1
    return string.replace(out,'</p></p>','</p>')

def genIndexPage():
    index_list = []
    al = archiveList(garticles.values())
    for y in al:
        for m in al[y]:
            for a in al[y][m]:
                #if len(index_list) < gconfig['index-count']:
                index_list.append(a)
    index_list.sort( key=lambda x: x.createdTime())
    index_list.reverse()
    out = gtemplate['index']['base']

    tcount = len(index_list)
    count = 0
    ccount = 0
    pcount = 0

    list_out = ''
    while count < tcount:
        a = index_list[count]
        list_out = list_out + gtemplate['index']['list-header']
        post_title = a.title()
        post_link = articlelinks[a.finfo['filename']]
        post_teaser = buildTeaser(a.content)
        list_out = list_out + gtemplate['index']['list-item']
        list_out = list_out + gtemplate['index']['list-footer']
        list_out = string.replace(list_out,'{link}',post_link)
        list_out = string.replace(list_out,'{post-title}',post_title)
        list_out = string.replace(list_out,'{post-teaser}',post_teaser)
        if ccount == gconfig['index-count']-1 or count == (tcount-1):
            ccount = 0
            if pcount == 0:
                fname = 'out/index.html'
            else:
                fname = string.replace('out/index{n}.html','{n}',str(pcount))
            fout = string.replace(out,'{body}',list_out + genIndexLinks(pcount,tcount))
            fout = expandMacros(fout)
            with open(fname,'wb') as fp:
                fp.write(fout)
            pcount = pcount + 1
            list_out = ''
        count = count + 1
        ccount = ccount + 1

def genIndexLinks(pcount,tcount):
    maxp = tcount / (gconfig['index-count']-1)
    wrapper = gtemplate['index']['links']['wrapper']
    if pcount == 0:
        nlinkr = '#'
    else:
        if pcount == 1:
            nlinkr = 'index.html'
        else:
            nlinkr = 'index' + str(pcount-1)+'.html'

    nlink = string.replace(gtemplate['index']['links']['next-page'],'{link}',nlinkr)

    if pcount == (maxp-1):
        plinkr = '#'
    else:
        plinkr = 'index' + str(pcount+1)+'.html'

    plink = string.replace(gtemplate['index']['links']['prev-page'],'{link}',plinkr)

    archive = string.replace(gtemplate['index']['links']['archive'],'{link}',gconfig['pages']['archive'])
    out = string.replace(wrapper,'{next-page}',nlink)
    fout = string.replace(out,'{prev-page}',plink)
    ret = string.replace(fout,'{archive}',archive)

    return ret

def main():
    global gtemplate
    global gconfig
    global gartids

    try:
        with open('config.json','rb') as fp:
            gconfig = json.load(fp)
    except IOError:
        print('Configuration not found, generating default configuration.')
        with open('config.json','wb') as fh:
            fh.write(default_config_file)
        with open('basic.json','wb') as fe:
            fe.write(default_template_file)
        with open('about.md','wb') as fa:
            fa.write(default_about_file)
        exit()

    with open(gconfig['template']+'.json','rb') as fp:
        gtemplate = json.load(fp)

    try:
        with open('index.json','rb') as fp:
            gartids = json.load(fp)
    except IOError:
        pass

    loadDefaults()
    c = getArticles()
    if os.path.exists('out') == False:
        os.mkdir('out')
    for f in c:
        art = c[f]
        gconfig['macros']['page-id'] = gartids[art.finfo['filename']]
        gconfig['macros']['permalink'] = string.replace(gconfig['base-url'] + '/' + articlelinks[f],' ','%20')
        out = expandMacros(prepareArticle(gtemplate['article'],art))
        gconfig['macros']['page-id'] = ''
        gconfig['macros']['permalink'] = ''
        with open('out/'+urllib.unquote(articlelinks[f]),'wb') as fh:
            fh.write(out)
    writeTags()
    makeArchive()
    genAboutPage()
    genIndexPage()
    writeAinfo()

def writeAinfo():
    with open('index.json','wb') as fp:
        json.dump(gartids,fp)

#TODO: files are not being cached
#TODO: only generate html when updates necessary (articles only)
if __name__ == '__main__':
    main()
