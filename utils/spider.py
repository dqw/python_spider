#! /usr/bin/env python
# -*- coding: utf-8 -*-

import urllib2
import re
import gzip
import chardet
import md5
from StringIO import StringIO
from BeautifulSoup import BeautifulSoup

def Spider(url, args):

    # 分析页面，获取链接
    def getLink(html):

        new_task = []

        soup = BeautifulSoup(html)
        for link in soup.findAll('a',
                attrs={'href': re.compile("^http://")}):
            href = link.get('href')
            new_task.append(href)

        return new_task 

    try:
        response = urllib2.urlopen(url, timeout=20)
        if response.info().get('Content-Encoding') == 'gzip':
            buf = StringIO(response.read())
            f = gzip.GzipFile(fileobj=buf)
            html = f.read()
        else:
            html = response.read()
    except urllib2.URLError as e:
        print 'url error'
        #self.logging.error("URLError:{0} {1}".format(url[1].encode("utf8"), e.reason))
    except urllib2.HTTPError as e:
        print 'http error'
        #self.logging.error("HTTPError:{0} {1}".format(url[1].encode("utf8"), e.code))
    except Exception as e:
        print 'exception'
        #self.logging.error("Unexpected:{0} {1}".format(url[1].encode("utf8"), str(e)))
    else:
        new_task = []

        if args.key == "":
            # 下载所有页面
            if url == 'http://www.baidu.com.cn':
                new_task = getLink(html)
        else:
            # 下载匹配关键字的页面
            if not self.encoding:
                charset = chardet.detect(html)
                self.encoding = charset['encoding']

            match = re.search(re.compile(self.key), html.decode(self.encoding, "ignore"))
            if match:
                new_task = getLink(url, html)
            else:
                print 'not match'
                #self.logging.debug("{0} ignore {1} key not match".format(self.getName(), url[1].encode("utf8")))


        return new_task 



