#! /usr/bin/env python
# -*- coding: utf-8 -*-

from utils.spider import GetHtml

class WorkManager(object):
    def __init__(self, queue_url, dict_downloaded, db, args, logging):
        self.threads = []
        self.queue_url = queue_url 
        self.dict_downloaded = dict_downloaded 
        self.db = db 
        self.args = args
        self.logging = logging 
        self.__init_thread_pool(args.thread)

    def __init_thread_pool(self, thread):
        for i in range(thread):
            self.threads.append(GetHtml(self.queue_url, self.dict_downloaded, self.db, self.args, self.logging))


