#! /usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import argparse
import threading
import Queue
import logging
import urllib2
import gzip
import re
import md5
import sqlite3
from StringIO import StringIO
from urlparse import urlparse
from BeautifulSoup import BeautifulSoup

class SaveHtml():
    def __init__(self, dbfile):
        self.dbfile = dbfile

        self.conn = sqlite3.connect(dbfile, check_same_thread = False)
        #设置支持中文存储
        self.conn.text_factory = str
        self.cmd = self.conn.cursor()
        self.cmd.execute('''
            create table if not exists data(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url text,
                url_hash text,
                deep INTEGER,
                html text
            )
        ''')
        self.conn.commit()

    def save(self, url, url_hash, deep, html):
        try:
            self.cmd.execute("insert into data (url, url_hash, deep, html) values (?,?,?,?)", (url, url_hash, deep, html))
            self.conn.commit()
        except Exception,e:
            print e

    def close(self):
        self.conn.close()

class GetHtml(threading.Thread):
    def __init__(self, queue_url, dict_url, dbfile, deep):
        threading.Thread.__init__(self)
        self.queue_url = queue_url
        self.dict_url = dict_url 
        self.dbfile = dbfile
        self.deep = deep
        self.save_html = SaveHtml(dbfile)

    def run(self):
        while True:
            url = self.queue_url.get()
            url_hash = md5.new(url[1]).hexdigest()
            logging.debug("{0} queue size {1}".format(self.getName(),
                self.queue_url.qsize()))

            if not self.dict_url.has_key(url_hash):
                self.dict_url[url_hash] = url[1]
                try:
                    response = urllib2.urlopen(url[1], timeout=5)
                    if response.info().get('Content-Encoding') == 'gzip':
                        buf = StringIO(response.read())
                        f = gzip.GzipFile(fileobj=buf)
                        html = f.read()
                    else:
                        html = response.read()
                except:
                    logging.error("Unexpected error:", sys.exc_info()[0])
                else:
                    if url[0] < self.deep:
                        soup = BeautifulSoup(html)
                        for link in soup.findAll('a',
                                attrs={'href': re.compile("^http://")}):
                            href = link.get('href')
                            self.queue_url.put([url[0]+1, href])
                            logging.debug("{0} add href {1} to queue".format(self.getName(), href.encode("utf8")))

                    self.save_html.save(url[1], url_hash, url[0], html)
                    logging.debug("{0} downloaded {1}".format(self.getName(), url[1].encode("utf8")))

            self.queue_url.task_done()


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('-u', dest="url", default="http://www.sina.com.cn", help="")
    parser.add_argument("-d", type=int, dest="deep", default=1, help="")  
    parser.add_argument("--thread", type=int, dest="thread", default=10, help="")  
    parser.add_argument('--dbfile', dest="dbfile", default="page.db", help="")
    parser.add_argument('--key', dest="key", default="", help="")
    parser.add_argument('-f', dest="logfile", default="spider.log", help="")
    parser.add_argument('-l', dest="loglevel", default="5", type=int, help="")
    parser.add_argument('--testself', dest="key", default="", help="")
    args = parser.parse_args()

    LEVELS = {
        1:logging.CRITICAL,
        2:logging.ERROR,
        3:logging.WARNING,
        4:logging.INFO,
        5:logging.DEBUG
    }
    level = LEVELS[args.loglevel]
    logging.basicConfig(filename=args.logfile,level=level)

    queue_url = Queue.Queue()
    queue_url.put([0, args.url])

    dict_url = {}

    for i in range(args.thread):
        thread_job = GetHtml(queue_url, dict_url, args.dbfile, args.deep)
        thread_job.setDaemon(True)
        thread_job.start()

    queue_url.join()
    print len(dict_url)

if __name__ == "__main__":
    main()
