#! /usr/bin/env python
# -*- coding: utf-8 -*-

import Queue
import logging
import urllib2
import md5
import sqlite3
import time
from utils.parser import get_args
from utils.pool import WorkManager
from utils.save import SaveToSqlite
from utils.log import PrintLog

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

if __name__ == "__main__":

    # 参数处理
    args = get_args()

    if args.testself:
        # 使用doctest进行测试
        import doctest
        doctest.testmod(verbose=True)
    else:
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

        db = SaveToSqlite(args.dbfile, logging)

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

