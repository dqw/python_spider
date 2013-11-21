#! /usr/bin/env python
# -*- coding: utf-8 -*-

import sqlite3

class SaveToSqlite():
    def __init__(self, dbfile, logging):
        self.dbfile = dbfile
        self.logging = logging
        self.conn = sqlite3.connect(dbfile, check_same_thread = False)
        #设置支持中文存储
        self.conn.text_factory = str
        self.cmd = self.conn.cursor()
        self.cmd.execute('''
            create table if not exists data(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url text,
                url_hash text,
                deep INTEGER,
                html text
            )
        ''')
        self.conn.commit()

    def save(self, url, url_hash, deep, html):
        try:
            self.cmd.execute("insert into data (url, url_hash, deep, html) values (?,?,?,?)", (url, url_hash, deep, html))
            self.conn.commit()
        except Exception as e:
            self.logging.error("Unexpected error:{0}".format(str(e)))

    def close(self):
        self.conn.close()

