import cx_Oracle
import os
import sqlite3

os.putenv('NLS_LANG', 'KOREAN_KOREA.KO16MSWIN949')

class Session(object):
    def __init__(self, sid, id, pwd, encoding='utf-8'):
        self.sid = sid
        self.id = id
        self.pwd = self.setPassword(pwd)
        self.encoding = encoding
        self.con = None
        self.cur = None

    def __getstate__(self):
        state = self.__dict__.copy()
        try:
            del state['con']
            del state['cur']
        except KeyError:
            pass
        return state

    def connection(self):
        try:
            if self.sid == 'demo.db':
                self.con = sqlite3.connect(self.sid, check_same_thread=False)
            elif self.sid == 'SWGS.JSD':
                self.con = sqlite3.connect(":memory:", check_same_thread=False)
            else:
                #print(self.id, self.pwd)
                self.con = cx_Oracle.connect(self.id, self.pwd, self.sid, encoding=self.encoding)
            # self.dbPool = cx_Oracle.SessionPool(user=self.id, password=self.passwd, dsn=dsn, min=1, max=10, increment=1)
        except cx_Oracle.DatabaseError as e:
            self.con = None
            raise Exception(e)

    def disconnection(self):
        if self.cur:
            self.cur.close()
            self.cur = None

        if self.con:
            self.con.close()
            self.con = None

    def setId(self, id):
        self.id = id

    def setPassword(self, pwd):
        return pwd.replace('\'', '\'\'')

    def setSid(self, sid):
        self.sid = sid

    def getId(self):
        return self.id

    def getPwd(self):
        return self.pwd

    def getSid(self):
        return self.sid

    def getCon(self):
        if self.con:
            self.connection()

        return self.con

    def getCursor(self):
        try:
            if self.con:
                cur = self.con.cursor()
                return cur
            else:
                return
        except AttributeError:
            self.connection()
            cur = self.con.cursor()
            return cur

    def getTnsInfo(self):
        print(os.environ['TNS_ADMIN'])