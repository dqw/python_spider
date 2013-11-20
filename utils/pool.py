#! /usr/bin/env python
# -*- coding: utf-8 -*-
from spider import GetHtml

class WorkManager(object):
    def __init__(self, args, queue_url, dict_downloaded, db, logging):
        self.threads = []
        self.args = args
        self.queue_url = queue_url
        self.dict_downloaded = dict_downloaded 
        self.db = db 
        self.logging = logging
        self.__init_thread_pool(args.thread)

    def __init_thread_pool(self, thread):
        for i in range(thread):
            self.threads.append(GetHtml(self.queue_url, self.dict_downloaded, self.db, self.args, self.logging))

    def check_queue(self):
        return self.queue_url.qsize()

    def wait_allcomplete(self):
        for item in self.threads:
            if item.isAlive():item.join()

