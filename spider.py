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
import chardet
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
    def __init__(self, queue_url, dict_downloaded, db, deep, key, encoding):
        threading.Thread.__init__(self)
        self.queue_url = queue_url
        self.dict_downloaded = dict_downloaded 
        self.db = db
        self.deep = deep
        self.key = key
        self.encoding = encoding

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
                logging.error("URLError:{0} {1}".format(url[1], e.reason))
            except urllib2.HTTPError as e:
                logging.error("HTTPError:{0} {1}".format(url[1], e.code))
            except Exception as e:
                logging.error("Unexpected:{0} {1}".format(url[1], str(e)))
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
                        logging.debug("{0} ignore {1} key not match".format(self.getName(), url[1].encode("utf8")))

            self.queue_url.task_done()

    def getLink(self, url, html):
        if url[0] < self.deep:
            if not soup:
                soup = BeautifulSoup(html)
            for link in soup.findAll('a',
                    attrs={'href': re.compile("^http://")}):
                href = link.get('href')
                url_hash = md5.new(href).hexdigest()
                if not self.dict_downloaded.has_key(url_hash):
                    self.queue_url.put([url[0]+1, href, url_hash])
                    logging.debug("{0} add href {1} to queue".format(self.getName(), href.encode("utf8")))

    def saveHtml(self, url, html):
        self.db.save(url[1], url[2], url[0], html)
        self.dict_downloaded[url[2]] = url[1]
        logging.debug("{0} downloaded {1}".format(self.getName(), url[1].encode("utf8")))

class PrintLog(threading.Thread):
    def __init__(self, queue_url, dict_downloaded):
        threading.Thread.__init__(self)
        self.queue_url = queue_url
        self.dict_downloaded = dict_downloaded 

    def run(self):
        while True:
            time.sleep(1)
            queue = self.queue_url.qsize()
            downloaded = len(self.dict_downloaded)
            print "queue:{0} downloaded:{1}".format(queue, downloaded)

# 测试网络连接
def test_network(url):
    """
    测试网络是否通常，返回200为测试通过
    >>> test_network("http://www.baidu.com")
    200
    """

    try:
        response = urllib2.urlopen(url)
    except urllib2.HTTPError as e:
        return e.code
    except Exception as e:
        return str(e)
    else:
        return response.getcode()

# 测试sqlite连接
def test_sqlite(dbfile):
    """
    测试是否可以创建并连接sqlite数据库文件，返回True为测试通过 
    >>> test_sqlite("test.db")
    True
    """

    try:
        conn = sqlite3.connect(dbfile)
    except Exception as e:
        return str(e)
    else:
        conn.close()
        return True

def main(url, deep, thread, dbfile, logfile, loglevel, key, encoding):
    start = time.time()

    # logging初始化，设定日志文件名和记录级别
    LEVELS = {
        1:logging.CRITICAL,
        2:logging.ERROR,
        3:logging.WARNING,
        4:logging.INFO,
        5:logging.DEBUG
    }
    level = LEVELS[loglevel]
    logging.basicConfig(filename=logfile, level=level)

    db = SaveHtml(dbfile)

    queue_url = Queue.Queue()
    queue_url.put([0, url, md5.new(url).hexdigest()])

    dict_downloaded = {}

    for i in range(thread):
        thread_job = GetHtml(queue_url, dict_downloaded, db, deep, key, encoding)
        thread_job.setDaemon(True)
        thread_job.start()

    thread_log = PrintLog(queue_url, dict_downloaded)
    thread_log.setDaemon(True)
    thread_log.start()

    queue_url.join()
    db.close()
    print "downloaded: {0} Elapsed Time: {1}".format(len(dict_downloaded), time.time()-start)

if __name__ == "__main__":

    # 参数处理
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', dest="url", default="http://www.baidu.com.cn", help="")
    parser.add_argument("-d", type=int, dest="deep", default=0, help="")  
    parser.add_argument("--thread", type=int, dest="thread", default=10, help="")  
    parser.add_argument('--dbfile', dest="dbfile", default="page.db", help="")
    parser.add_argument('-f', dest="logfile", default="spider.log", help="")
    parser.add_argument('-l', dest="loglevel", default="5", type=int, help="")
    parser.add_argument('--key', dest="key", default="", help="")
    parser.add_argument('--encoding', dest="encoding", default=None, help="")
    parser.add_argument('--testself', action="store_true", dest="testself", default="", help="")
    args = parser.parse_args()

    if args.testself:
        # 使用doctest进行测试
        import doctest
        doctest.testmod(verbose=True)
    else:
        args.key = args.key.decode("utf-8")
        main(args.url, args.deep, args.thread, args.dbfile, args.logfile, args.loglevel, args.key, args.encoding)
