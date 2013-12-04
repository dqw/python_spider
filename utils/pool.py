#! /usr/bin/env python
# -*- coding: utf-8 -*-

class WorkManager(object):
    def __init__(self, work, thread):
        self.threads = []
        self.work = work
        self.__init_thread_pool(thread)

    def __init_thread_pool(self, thread):
        for i in range(thread):
            self.threads.append(self.work)

    def wait_allcomplete(self):
        for item in self.threads:
            if item.isAlive():item.join()

