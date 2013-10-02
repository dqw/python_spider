#! /usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import argparse
import threading
import urllib2
import gzip
import re
import Queue
import sqlite3
import logging
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
                deep INTEGER,
                url text,
                html text
            )
        ''')
        self.conn.commit()

    def save(self, deep, url, html):
        try:
            self.cmd.execute("insert into data (deep, url, html) values (?,?,?)", (deep, url, html))
            self.conn.commit()
        except Exception,e:
            print e

    def close(self):
        self.conn.close()

class GetHtml(threading.Thread):
    def __init__(self, queue_url, dbfile, deep):
        threading.Thread.__init__(self)
        self.queue_url = queue_url
        self.dbfile = dbfile
        self.deep = deep
        self.save_html = SaveHtml(dbfile)

    def run(self):
        while True:
            try:
                url = self.queue_url.get()

                logging.debug("{0} queue size {1}".format(self.getName(),
                    self.queue_url.qsize()))

                response = urllib2.urlopen(url[1], timeout=5)

                if response.info().get('Content-Encoding') == 'gzip':
                    buf = StringIO(response.read())
                    f = gzip.GzipFile(fileobj=buf)
                    html = f.read()
                else:
                    html = response.read()

                if url[0] < 1:
                    soup = BeautifulSoup(html)
                    for link in soup.findAll('a',
                            attrs={'href': re.compile("^http://")}):
                        href = link.get('href')
                        logging.debug("{0} add href {1} to queue".format(self.getName(), href.encode("utf8")))
                        self.queue_url.put([url[0]+1, href])
                self.save_html.save(url[0], url[1], html)
                logging.debug("{0} downloaded {1}".format(self.getName(), url[1].encode("utf8")))
            except:
                logging.error("Unexpected error:", sys.exc_info()[0])

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

    for i in range(2):
        thread_job = GetHtml(queue_url, args.dbfile, args.deep)
        thread_job.setDaemon(True)
        thread_job.start()

    queue_url.join()

if __name__ == "__main__":
    main()
