#! /usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import urllib2
import sqlite3
import time
from utils.parser import get_args
from utils.pool import ThreadPool
from utils.spider import spider


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
            1: logging.CRITICAL,
            2: logging.ERROR,
            3: logging.WARNING,
            4: logging.INFO,
            5: logging.DEBUG
        }
        level = LEVELS[args.loglevel]
        logging.basicConfig(filename=args.logfile, level=level)

        if args.url != '':
            # 初始化线程池，开始工作
            thread_pool = ThreadPool(args.thread, args)
            thread_pool.add_task(spider, args.url, 0)
            thread_pool.start_task()
            thread_pool.wait_all_complete()

            # 完成后打印信息
            progress_info = thread_pool.get_progress_info()
            print "总任务数：", progress_info['tasks_number']
            print "成功下载：", progress_info['success']
            print "下载失败：", progress_info['failure']
            print "花费时间： {0} 秒".format(time.time()-start)
        else:
            logging.critical("No initial url")
            print "请使用-u参数指定初始url"
