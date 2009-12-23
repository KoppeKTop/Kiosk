#!/usr/bin/env python
import MySQLdb as DB
from configs import DBInfo
from kiosklog import logger

class SQLWorker(object):
    def __init__(self):
        pass
            
    def execute(self, query):
        try:
            db = DB.connect(host=DBInfo.db_host, 
                                 user = DBInfo.db_user, 
                                 passwd = DBInfo.db_pwd,
                                 db=DBInfo.db_name)
            curr = db.cursor()
        except  Exception, e:
            logger.error('in SQLWorker.execute %s' % (e.message,))
        curr.execute(query)
        return curr.fetchall()
