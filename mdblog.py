#mdblog
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
    "article":"{tpage-head-start}{title} | {site-title}{tpage-head-end}{header}<h2>{title}</h2><div id=\"byline\"><p>Posted {date} by <em>{author}</em></p></div><div id=\"content\">{article}</div><div id=\"tags\"><p>Filed under: {tags}</p><p><a href=\"{permalink}\">Permalink</a></p></div>{footer}{html-end}",
    "taglist": {
        "base":"{tpage-head-start}Post Categories of {site-title}{tpage-head-end}{header}<h2>Post Categories</h2><div id=\"content\">{body}</div>{footer}{html-end}",
        "section-start":"<a name=\"{tag}\"><h3>{tag}</h3></a><div>",
        "list-header":"<ul>",
        "list-item":"<li><a href=\"{link}\">{link-title}</a></li>",
        "list-footer":"</ul>",
        "section-end":"</div>"
        },
    "index": {
        "base":"{tpage-head-start}{site-title}{tpage-head-end}{header}<h2>Recent Posts</h2><div id=\"content\">{body}</div><div id=\"more\"><a href=\"{page-archive}\">Archives</a></div>{footer}{html-end}",
        "list-header":"<div id=\"entry-title\">",
        "list-item":"<h2><a href=\"{link}\">{post-title}</a></h2><div id=\"entry-teaser\">{post-teaser}</div>",
        "list-footer":"</div>"
    },
    "macros": {
        "header":"<div id=\"header\"><h1><a href=\"{page-index}\">{site-title}</a></h1></div>",
        "footer":"<div id=\"footer\">{copy}</div>",
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

    output = string.replace(base,'{body}',listout)
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

#TODO: make more generic so can be used to generate for specified timeframe
def makeArchive():
    al = archiveList(garticles.values())
    with open('out/'+gconfig['pages']['archive'],'wb') as fh:
        fh.write('<html><head><title>Archive | ' + gconfig['site-title'] + '</title></head><body>')
        for y in al:
            fh.write('<h1>'+str(y)+'</h1>')
            for m in al[y]:
                fh.write("<h2>"+str(m)+'</h2>')
                for i in al[y][m]:
                    fh.write('<a href="'+articlelinks[i.finfo['filename']]+'">'+i.title()+'</a><br />')
        fh.write('</body></html>')

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
        gconfig['macros']['author'] = '<a href="'+gconfig['pages']['about']['output']+'">'+gconfig['author']+'</a>'
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
                if len(index_list) < gconfig['index-count']:
                    index_list.append(a)

    out = gtemplate['index']['base']

    list_out = ''
    for a in index_list:
        list_out = list_out + gtemplate['index']['list-header']
        post_title = a.title()
        post_link = articlelinks[a.finfo['filename']]
        post_teaser = buildTeaser(a.content)
        list_out = list_out + gtemplate['index']['list-item']
        list_out = list_out + gtemplate['index']['list-footer']
        list_out = string.replace(list_out,'{link}',post_link)
        list_out = string.replace(list_out,'{post-title}',post_title)
        list_out = string.replace(list_out,'{post-teaser}',post_teaser)

    out = string.replace(out,'{body}',list_out)
    out = expandMacros(out)

    with open('out/index.html','wb') as fp:
        fp.write(out)

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


if __name__ == '__main__':
    main()
