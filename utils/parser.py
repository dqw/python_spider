#! /usr/bin/env python
# -*- coding: utf-8 -*-

import argparse

def get_args():
    # 参数处理
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', dest="url", default="http://www.baidu.com.cn", help="")
    parser.add_argument("-d", type=int, dest="deep", default=0, help="")  
    parser.add_argument("--thread", type=int, dest="thread", default=2, help="")  
    parser.add_argument('--dbfile', dest="dbfile", default="page.db", help="")
    parser.add_argument('-f', dest="logfile", default="spider.log", help="")
    parser.add_argument('-l', dest="loglevel", default="5", type=int, help="")
    parser.add_argument('--key', dest="key", default="", help="")
    parser.add_argument('--encoding', dest="encoding", default=None, help="")
    parser.add_argument('--testself', action="store_true", dest="testself", default="", help="")
    args = parser.parse_args()
    args.key = args.key.decode("utf-8")

    return args

