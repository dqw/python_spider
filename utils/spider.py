#! /usr/bin/env python
# -*- coding: utf-8 -*-

import threading
import urllib2
import re
import gzip
import chardet
import md5
from StringIO import StringIO
from BeautifulSoup import BeautifulSoup

class GetHtml(threading.Thread):
    def __init__(self, queue_url, dict_downloaded, db, args, logging):
        threading.Thread.__init__(self)
        self.queue_url = queue_url
        self.dict_downloaded = dict_downloaded 
        self.db = db
        self.deep = args.deep 
        self.key = args.key
        self.encoding = args.encoding
        self.logging = logging
        self.daemon = True
        self.start()

    def run(self):
        while True:
            url = self.queue_url.get()
            try:
                response = urllib2.urlopen(url[1], timeout=20)
                if response.info().get('Content-Encoding') == 'gzip':
                    buf = StringIO(response.read())
                    f = gzip.GzipFile(fileobj=buf)
                    html = f.read()
                else:
                    html = response.read()
            except urllib2.URLError as e:
                self.logging.error("URLError:{0} {1}".format(url[1].encode("utf8"), e.reason))
            except urllib2.HTTPError as e:
                self.logging.error("HTTPError:{0} {1}".format(url[1].encode("utf8"), e.code))
            except Exception as e:
                self.logging.error("Unexpected:{0} {1}".format(url[1].encode("utf8"), str(e)))
            else:
                if self.key == "":
                    self.getLink(url, html)
                    self.saveHtml(url, html)
                else:
                    if not self.encoding:
                        charset = chardet.detect(html)
                        self.encoding = charset['encoding']

                    match = re.search(re.compile(self.key), html.decode(self.encoding, "ignore"))
                    if match:
                        self.getLink(url, html)
                        self.saveHtml(url, html)
                    else:
                        self.logging.debug("{0} ignore {1} key not match".format(self.getName(), url[1].encode("utf8")))

            self.queue_url.task_done()

    def getLink(self, url, html):
        if url[0] < self.deep:
            soup = BeautifulSoup(html)
            for link in soup.findAll('a',
                    attrs={'href': re.compile("^http://")}):
                href = link.get('href')
                url_hash = md5.new(href.encode("utf8")).hexdigest()
                if not self.dict_downloaded.has_key(url_hash):
                    self.queue_url.put([url[0]+1, href, url_hash])
                    self.logging.debug("{0} add href {1} to queue".format(self.getName(), href.encode("utf8")))

    def saveHtml(self, url, html):
        self.db.save(url[1], url[2], url[0], html)
        self.dict_downloaded[url[2]] = url[1]
        self.logging.debug("{0} downloaded {1}".format(self.getName(), url[1].encode("utf8")))

