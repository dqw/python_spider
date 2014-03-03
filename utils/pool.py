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
        self.__initThreadPool(thread_num)

    def __initThreadPool(self, thread_num):
        for i in range(thread_num):
            self.threads.append(WorkThread(self))

    def addTask(self, func, url):
        self.work_queue.put((func, url))

    def getTask(self):
        #只使用一个线程,能正常退出
        task = self.work_queue.get(block=False)
        #多线程但是不退出
        #task = self.work_queue.get()

        return task

    def taskDone(self):
        self.work_queue.task_done()

    def startTask(self):
        for item in self.threads:
            item.start()

    def increaseRunning(self):
        self.running += 1

    def decreaseRunning(self):
        self.running -= 1

    def getRunning(self):
        return self.running

    def checkQueue(self):
        return self.work_queue.qsize()

    def waitAllComplete(self):
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
                do, url = self.thread_pool.getTask()
                self.thread_pool.increaseRunning()
                print "{0} downloaded {1} \n".format(threading.current_thread(), url)
                new_task = do(url, self.thread_pool.args)
                if new_task:
                    for url in new_task:
                        self.thread_pool.addTask(do, url)

                self.thread_pool.decreaseRunning()
                self.thread_pool.taskDone()
            except Queue.Empty:
                if self.thread_pool.getRunning() <= 0:
                    break
            except Exception,e:
                print str(e)
                break

