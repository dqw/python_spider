#! /usr/bin/env python
# -*- coding: utf-8 -*-

import threading
import Queue
import sqlite3
import logging


# 保存html
class SaveToSqlite(threading.Thread):
    def __init__(self, thread_pool, dbfile):
        threading.Thread.__init__(self)
        self.thread_pool = thread_pool
        self.conn = sqlite3.connect(dbfile, check_same_thread=False)
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

    def run(self):
        while True:
            try:
                url, html = self.thread_pool.get_save_task()
                try:
                    self.cmd.execute("insert into data (url, html) values (?,?)", (url, html))
                    self.conn.commit()
                except Exception as e:
                    logging.error("Save error:{0}".format(str(e)))
            except Queue.Empty:
                thread_number = self.thread_pool.get_running()
                if thread_number <= 0:
                    self.conn.close()
                    break
            except Exception, e:
                print str(e)
                break
