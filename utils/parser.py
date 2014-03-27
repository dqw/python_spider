#! /usr/bin/env python
# -*- coding: utf-8 -*-

import argparse


def get_args():
    # 参数处理
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', dest="url", default="", help="爬虫起始地址")
    parser.add_argument("-d", type=int, dest="deep", default=0, help="爬取深度，起始地址为第0级")  
    parser.add_argument("--thread", type=int, dest="thread", default=10, help="爬虫使用的线程数")  
    parser.add_argument('--dbfile', dest="dbfile", default="spider.db", help="存放数据库（sqlite）文件名")
    parser.add_argument('-f', dest="logfile", default="spider.log", help="日志文件名")
    parser.add_argument('-l', dest="loglevel", default="5", type=int, help="日志记录文件记录详细程度，数字越大记录越详细(1-5)")
    parser.add_argument('--key', dest="key", default="", help="页面内的关键词，获取满足该关键词的网页，不指定关键字时获取所有页面")
    parser.add_argument('--encoding', dest="encoding", default=None, help="指定页面编码，如果不指定将自动测试页面编码")
    parser.add_argument('--testself', action="store_true", dest="testself", default="", help="程序自测自测")
    args = parser.parse_args()
    args.key = args.key.decode("utf-8")

    return args
