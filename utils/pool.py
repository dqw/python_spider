#! /usr/bin/env python
# -*- coding: utf-8 -*-

import threading
import Queue
import md5
import logging
import time
import sqlite3

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
        # 开始保存html
        SaveToSqlite(self, self.args.dbfile)

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
            thread_number = self.thread_pool.get_running()
            if thread_number <= 0:
                break

            progress_info = self.thread_pool.get_progress_info()

            print '总任务数:', progress_info['tasks_number'] 
            print '下载中:', thread_number
            print '待下载:', progress_info['work_queue_number'] 
            print '待保存:', progress_info['save_queue_number'] 
            print '---------------------------------------' 

            time.sleep(10)

# 保存html
class SaveToSqlite(threading.Thread):
    def __init__(self, thread_pool, dbfile):
        threading.Thread.__init__(self)
        self.thread_pool = thread_pool
        self.conn = sqlite3.connect(dbfile, check_same_thread = False)
        #设置支持中文存储
        self.conn.text_factory = str
        self.cmd = self.conn.cursor()
        self.cmd.execute('''
            create table if not exists data(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url text,
                html text
            )
        ''')
        self.conn.commit()
        self.start()

    def run(self):
        while True:
            try:
                url, html = self.thread_pool.get_save_task()
                try:
                    self.cmd.execute("insert into data (url, html) values (?,?)", (url, html))
                    self.conn.commit()
                except Exception as e:
                    logging.error("Unexpected error:{0}".format(str(e)))
            except Queue.Empty:
                thread_number = self.thread_pool.get_running()
                if thread_number <= 0:
                    self.conn.close()
                    break
            except Exception,e:
                print str(e)
                break


