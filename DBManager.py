'''
Created on Apr 24, 2016

@author: brian
'''

import sqlite3
from __builtin__ import str

class DatabaseManager(object):
    def __init__(self, db):
        self.conn = sqlite3.connect(db)
        self.conn.text_factory = str
        self.conn.execute('pragma foreign_keys = on')
        self.conn.commit()
        self.cur = self.conn.cursor()

    def query(self, arg,skipCommit=0):
        self.cur.execute(arg)
        if not skipCommit: self.conn.commit()
        return self.cur
    
    def execSQL(self, arg, paramArr=None):
        self.cur.execute(arg,paramArr)
        return self.cur

    def __del__(self):
        self.conn.close()