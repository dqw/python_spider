#! /usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import threading
import argparse
import Queue
import logging
import urllib2
import md5
import gzip
import sqlite3
import time
import chardet
from StringIO import StringIO
from urlparse import urlparse
from utils.pool import WorkManager

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

def main(args):
    start = time.time()

    # logging初始化，设定日志文件名和记录级别
    LEVELS = {
        1:logging.CRITICAL,
        2:logging.ERROR,
        3:logging.WARNING,
        4:logging.INFO,
        5:logging.DEBUG
    }
    level = LEVELS[args.loglevel]
    logging.basicConfig(filename=args.logfile, level=level)

    db = SaveHtml(args.dbfile)

    queue_url = Queue.Queue()
    queue_url.put([0, args.url, md5.new(args.url).hexdigest()])

    dict_downloaded = {}

    thread_log = PrintLog(queue_url, dict_downloaded)
    thread_log.setDaemon(True)
    thread_log.start()

    work_manager = WorkManager(args, queue_url, dict_downloaded, db, logging)
    work_manager.wait_allcomplete()

    db.close()
    print "downloaded: {0} Elapsed Time: {1}".format(len(dict_downloaded), time.time()-start)

if __name__ == "__main__":

    # 参数处理
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', dest="url", default="http://www.baidu.com.cn", help="")
    parser.add_argument("-d", type=int, dest="deep", default=0, help="")  
    parser.add_argument("--thread", type=int, dest="thread", default=1, help="")  
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
        main(args)
