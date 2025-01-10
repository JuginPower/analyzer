import sqlite3


class SqliteDatamanager:

    def __init__(self, database_name: str):

        self.connection_string = database_name

    def init_conn(self):

        try:
            conn = sqlite3.connect(self.connection_string)
        except sqlite3.Error as err:
            raise err
        else:
            list_tables = conn.execute("select name from sqlite_master where type='table';").fetchall()

            if len(list_tables) < 2:
                raise NameError(f"Database File: {self.connection_string}; does not exist and opened for the first time!")

            return conn

    def select(self, sqlstring) -> list:

        mydb = self.init_conn()
        mycursor = mydb.cursor()

        try:
            mycursor.execute(sqlstring)
        except sqlite3.Error as err:
            raise err

        result = mycursor.fetchall()
        mydb.close()
        return result

    def query(self, sqlstring, val=None) -> int:

        mydb = self.init_conn()
        mycursor = mydb.cursor()

        try:
            if isinstance(val, list):
                mycursor.executemany(sqlstring, val)
            elif isinstance(val, tuple):
                mycursor.execute(sqlstring, val)
            elif not val:
                mycursor.execute(sqlstring)

        except sqlite3.Error as err:
            raise err

        mydb.commit()
        mydb.close()
        return mycursor.rowcount
    
