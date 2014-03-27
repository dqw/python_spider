#! /usr/bin/env python
# -*- coding: utf-8 -*-

import threading
import Queue
import md5
import logging
from utils.progress import PrintProgress
from utils.save import SaveToSqlite


class ThreadPool(object):
    def __init__(self, thread_num, args):

        self.args = args
        self.work_queue = Queue.Queue()
        self.save_queue = Queue.Queue()
        self.threads = []
        self.running = 0
        self.failure = 0
        self.success = 0
        self.tasks = {}
        self.thread_name = threading.current_thread().getName()
        self.__init_thread_pool(thread_num)

    # 线程池初始化
    def __init_thread_pool(self, thread_num):
        # 下载线程
        for i in range(thread_num):
            self.threads.append(WorkThread(self))
        # 打印进度信息线程
        self.threads.append(PrintProgress(self))
        # 保存线程
        self.threads.append(SaveToSqlite(self, self.args.dbfile))

    # 添加下载任务
    def add_task(self, func, url, deep):
        # 记录任务，判断是否已经下载过
        url_hash = md5.new(url.encode("utf8")).hexdigest()
        if not url_hash in self.tasks:
            self.tasks[url_hash] = url
            self.work_queue.put((func, url, deep))
            logging.info("{0} add task {1}".format(self.thread_name, url.encode("utf8")))

    # 获取下载任务
    def get_task(self):
        task = self.work_queue.get(block=False)

        return task

    def task_done(self):
        self.work_queue.task_done()

    # 开始任务
    def start_task(self):
        for item in self.threads:
            item.start()

        logging.debug("Work start")

    def increase_success(self):
        self.success += 1

    def increase_failure(self):
        self.failure += 1

    def increase_running(self):
        self.running += 1

    def decrease_running(self):
        self.running -= 1

    def get_running(self):
        return self.running

    def get_progress_info(self):
        progress_info = {}
        progress_info['work_queue_number'] = self.work_queue.qsize()
        progress_info['tasks_number'] = len(self.tasks)
        progress_info['save_queue_number'] = self.save_queue.qsize()
        progress_info['success'] = self.success
        progress_info['failure'] = self.failure

        return progress_info

    def add_save_task(self, url, html):
        self.save_queue.put((url, html))

    def get_save_task(self):
        save_task = self.save_queue.get(block=False)

        return save_task

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

                if html == '':
                    self.thread_pool.increase_failure()
                else:
                    self.thread_pool.increase_success()
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
            except Exception, e:
                print str(e)
                break
