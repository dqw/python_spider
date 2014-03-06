#! /usr/bin/env python
# -*- coding: utf-8 -*-

import threading
import Queue
import md5
import logging
import time

class ThreadPool(object):
    def __init__(self, thread_num, args):

        self.args = args
        self.work_queue = Queue.Queue()
        self.save_queue = Queue.Queue()
        self.threads = []
        self.running = 0
        self.tasks = {}
        self.__init_thread_pool(thread_num)

    def __init_thread_pool(self, thread_num):
        for i in range(thread_num):
            self.threads.append(WorkThread(self))

    def add_task(self, func, url, deep):
        # 记录任务，判断是否已经下载过
        url_hash = md5.new(url.encode("utf8")).hexdigest()
        if not self.tasks.has_key(url_hash):
            self.tasks[url_hash] = url
            self.work_queue.put((func, url, deep))

    def get_task(self):
        #只使用一个线程,能正常退出
        task = self.work_queue.get(block=False)

        return task

    def task_done(self):
        self.work_queue.task_done()

    # 开始任务
    def start_task(self):
        for item in self.threads:
            item.start()

        # 开始打印进度信息
        PrintProgress(self)


    def increase_running(self):
        self.running += 1

    def decrease_running(self):
        self.running -= 1

    def get_running(self):
        return self.running

    def get_progress_info(self):
        return self.work_queue.qsize(), len(self.tasks), self.save_queue.qsize()

    def add_save_task(self, url, html):
        self.save_queue.put((url, html))

    def wait_all_complete(self):
        for item in self.threads:
            if item.isAlive():
                item.join()

class WorkThread(threading.Thread):
    def __init__(self, thread_pool):
        threading.Thread.__init__(self)
        self.thread_pool = thread_pool

    def run(self):
        while True:
            try:
                do, url, deep = self.thread_pool.get_task()
                self.thread_pool.increase_running()

                # 判断deep，是否获取新的链接
                flag_get_new_link = True
                if deep >= self.thread_pool.args.deep:
                    flag_get_new_link = False

                html, new_link = do(url, self.thread_pool.args, flag_get_new_link)

                # html添加到待保存队列
                self.thread_pool.add_save_task(url, html)

                # 添加新任务
                if new_link:
                    for url in new_link:
                        self.thread_pool.add_task(do, url, deep + 1)

                self.thread_pool.decrease_running()
                self.thread_pool.task_done()
            except Queue.Empty:
                if self.thread_pool.get_running() <= 0:
                    break
            except Exception,e:
                print str(e)
                break


# 打印进度信息
class PrintProgress(threading.Thread):
    def __init__(self, thread_pool):
        threading.Thread.__init__(self)
        self.thread_pool = thread_pool
        self.start()

    def run(self):
        while True:
            thread_num = self.thread_pool.get_running()
            if thread_num <= 0:
                break

            work_queue_num, tasks_number, save_queue_number = self.thread_pool.get_progress_info()

            print '下载中:', thread_num
            print '待下载:', work_queue_num 
            print '已下载:', save_queue_number 
            print '总任务数:', tasks_number 
            print '---------------------------------------' 

            time.sleep(1)
