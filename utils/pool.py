#! /usr/bin/env python
# -*- coding: utf-8 -*-

import threading
import Queue

class ThreadPool(object):
    def __init__(self, thread_num, args):

        self.args = args
        self.work_queue = Queue.Queue()
        self.threads = []
        self.running = 0
        self.__init_thread_pool(thread_num)

    def __init_thread_pool(self, thread_num):
        for i in range(thread_num):
            self.threads.append(WorkThread(self))

    def add_task(self, func, url):
        self.work_queue.put((func, url))

    def get_task(self):
        #只使用一个线程,能正常退出
        task = self.work_queue.get(block=False)
        #多线程但是不退出
        #task = self.work_queue.get()

        return task

    def task_done(self):
        self.work_queue.task_done()

    def start_task(self):
        for item in self.threads:
            item.start()

    def increase_running(self):
        self.running += 1

    def decrease_running(self):
        self.running -= 1

    def get_running(self):
        return self.running

    def check_queue(self):
        return self.work_queue.qsize()

    def wait_all_complete(self):
        for item in self.threads:
            if item.isAlive():
                item.join()

class WorkThread(threading.Thread):
    def __init__(self, thread_pool):
        threading.Thread.__init__(self)
        self.thread_pool = thread_pool
        self.stop = False

    def run(self):
        while True:
            try:
                do, url = self.thread_pool.get_task()
                self.thread_pool.increase_running()
                print "{0} downloaded {1} \n".format(threading.current_thread(), url)
                new_task = do(url, self.thread_pool.args)
                if new_task:
                    for url in new_task:
                        self.thread_pool.add_task(do, url)

                self.thread_pool.decrease_running()
                self.thread_pool.task_done()
            except Queue.Empty:
                if self.thread_pool.get_running() <= 0:
                    break
            except Exception,e:
                print str(e)
                break

