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
import time
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
        except Exception as e:
            logging.error("Unexpected error:{0}".format(str(e)))

    def close(self):
        self.conn.close()

class GetHtml(threading.Thread):
    def __init__(self, queue_url, dict_url, db, deep):
        threading.Thread.__init__(self)
        self.queue_url = queue_url
        self.dict_url = dict_url 
        self.db = db
        self.deep = deep

    def run(self):
        while True:
            url = self.queue_url.get()
            url_hash = md5.new(url[1]).hexdigest()
            if not self.dict_url.has_key(url_hash):
                try:
                    response = urllib2.urlopen(url[1], timeout=20)
                    if response.info().get('Content-Encoding') == 'gzip':
                        buf = StringIO(response.read())
                        f = gzip.GzipFile(fileobj=buf)
                        html = f.read()
                    else:
                        html = response.read()
                except urllib2.URLError as e:
                    logging.error("URLError:{0} {1}".format(url[1], e.reason))
                except urllib2.HTTPError as e:
                    logging.error("HTTPError:{0} {1}".format(url[1], e.code))
                except Exception as e:
                    logging.error("Unexpected:{0} {1}".format(url[1], str(e)))
                else:
                    self.dict_url[url_hash] = url[1]
                    if url[0] < self.deep:
                        soup = BeautifulSoup(html)
                        for link in soup.findAll('a',
                                attrs={'href': re.compile("^http://")}):
                            href = link.get('href')
                            self.queue_url.put([url[0]+1, href])
                            logging.debug("{0} add href {1} to queue".format(self.getName(), href.encode("utf8")))

                    self.db.save(url[1], url_hash, url[0], html)
                    logging.debug("{0} downloaded {1}".format(self.getName(), url[1].encode("utf8")))

            self.queue_url.task_done()

class PrintLog(threading.Thread):
    def __init__(self, queue_url, dict_url):
        threading.Thread.__init__(self)
        self.queue_url = queue_url
        self.dict_url = dict_url 

    def run(self):
        while True:
            time.sleep(1)
            queue = self.queue_url.qsize()
            downloaded = len(self.dict_url)
            total = queue + downloaded
            print "queue:{0} downloaded:{1} total:{2}".format(queue, downloaded, total)

def main():
    start = time.time()

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

    db = SaveHtml(args.dbfile)

    queue_url = Queue.Queue()
    queue_url.put([0, args.url])

    dict_url = {}

    for i in range(args.thread):
        thread_job = GetHtml(queue_url, dict_url, db, args.deep)
        thread_job.setDaemon(True)
        thread_job.start()

    thread_log = PrintLog(queue_url, dict_url)
    thread_log.setDaemon(True)
    thread_log.start()

    queue_url.join()
    print "downloaded: {0} Elapsed Time: {1}".format(len(dict_url), time.time()-start)

if __name__ == "__main__":
    main()
