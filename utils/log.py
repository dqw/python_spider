#! /usr/bin/env python
# -*- coding: utf-8 -*-

import threading
import time

class PrintLog(threading.Thread):
    def __init__(self, queue_url, dict_downloaded):
        threading.Thread.__init__(self)
        self.queue_url = queue_url
        self.dict_downloaded = dict_downloaded 

    def run(self):
        while True:
            if self.queue_url.empty():
                break
            time.sleep(1)
            queue = self.queue_url.qsize()
            downloaded = len(self.dict_downloaded)
            print "queue:{0} downloaded:{1}".format(queue, downloaded)

