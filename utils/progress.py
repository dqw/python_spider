#! /usr/bin/env python
# -*- coding: utf-8 -*-

import threading
import time
import logging


# 打印进度信息
class PrintProgress(threading.Thread):
    def __init__(self, thread_pool):
        threading.Thread.__init__(self)
        self.thread_pool = thread_pool

    def run(self):
        while True:
            thread_number = self.thread_pool.get_running()
            progress_info = self.thread_pool.get_progress_info()

            if thread_number <= 0 and progress_info['save_queue_number'] <= 0:
                break

            print '总任务数:', progress_info['tasks_number']
            print '工作线程:', thread_number
            print '待下载:', progress_info['work_queue_number']
            print '待保存:', progress_info['save_queue_number']
            print '---------------------------------------'

            logging.debug("Print progress")

            time.sleep(10)
