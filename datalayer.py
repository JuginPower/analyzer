import sqlite3

sql_script = """
BEGIN TRANSACTION;
DROP TABLE IF EXISTS "indiz";
CREATE TABLE IF NOT EXISTS "indiz" (
	"indiz_id"	integer NOT NULL,
	"name"	text NOT NULL,
	PRIMARY KEY("indiz_id" AUTOINCREMENT)
);
DROP TABLE IF EXISTS "kategorien";
CREATE TABLE IF NOT EXISTS "kategorien" (
	"name"	TEXT NOT NULL,
	"kid"	INTEGER NOT NULL,
	PRIMARY KEY("kid" AUTOINCREMENT)
);
DROP TABLE IF EXISTS "keywords";
CREATE TABLE IF NOT EXISTS "keywords" (
	"kid"	INTEGER NOT NULL,
	"name"	TEXT NOT NULL,
	FOREIGN KEY("kid") REFERENCES "kategorien"("kid")
);
DROP TABLE IF EXISTS "data";
CREATE TABLE IF NOT EXISTS "data" (
	"date"	TEXT NOT NULL,
	"indiz_id"	INTEGER NOT NULL,
	"open"	REAL,
	"high"	REAL,
	"low"	REAL,
	"close"	REAL,
	FOREIGN KEY("indiz_id") REFERENCES "indiz" on update CASCADE on DELETE cascade
);
COMMIT;
"""

class SqliteDatamanager:

    def __init__(self, database_name: str):

        self.connection_string = database_name

    def init_database(self, conn: sqlite3.Connection):

        try:
            cursor = conn.cursor()
            cursor.executescript(sql_script)
        except sqlite3.Error as err:
            raise err
        else:
            cursor.close()
            conn.commit()

    def init_conn(self):

        try:
            conn = sqlite3.connect(self.connection_string)
        except sqlite3.Error as err:
            raise err
        else:
            list_tables = conn.execute("select name from sqlite_master where type='table';").fetchall()

            if len(list_tables) < 2:
                self.init_database(conn)

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
    
