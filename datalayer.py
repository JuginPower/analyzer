import sqlite3
from datetime import datetime


class Datamanager:

    def __init__(self, connection="finance.sqlite3"):

        self.connection_string = connection

    def init_conn(self):

        return sqlite3.connect(self.connection_string)

    def select(self, sqlstring) -> list:

        mydb = self.init_conn()
        mycursor = mydb.cursor()

        try:
            mycursor.execute(sqlstring)
        except sqlite3.OperationalError as err:
            print(datetime.now())
            print(err.args)

        result = mycursor.fetchall()
        mydb.close()
        return result

    def query(self, sqlstring, val=None) -> int:

        mydb = self.init_conn()
        mycursor = mydb.cursor()

        if isinstance(val, list):
            mycursor.executemany(sqlstring, val)
        elif isinstance(val, tuple):
            mycursor.execute(sqlstring, val)
        elif not val:
            mycursor.execute(sqlstring)

        mydb.commit()
        mydb.close()
        return mycursor.rowcount
    
