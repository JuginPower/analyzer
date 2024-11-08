import requests
from requests.auth import HTTPBasicAuth
from datalayer import Datamanager
from pathlib import Path
import os


BASE_DIR = Path(__file__).resolve().parent.parent
database_file = os.path.join(BASE_DIR, "finance.sqlite3")
dm = Datamanager(database_file)

def check_presence(tablename: str, column: str, filtername: str):
    result = dm.select(f"select {column} from {tablename} where {column}='{filtername}';")
    if len(result) == 0:
        return False
    return True


url = "https://eugenkraft.com/stock"
username = "eugen"
passwd = "F9^q5(4lY:9}pm"

res = requests.get(url, auth=HTTPBasicAuth(username, passwd))
list_tables = dm.select("select name from sqlite_master where type='table';")

if len(list_tables) < 2:
    raise NameError(f"Database File: {database_file}; does not exist and opened for the first time!")

elif 299 > res.status_code >= 200:
    data_source = res.json()
    for item in data_source:
        data = item.get("data")
        datum = item.get("datum")
        indiz = item.get("indiz")

        if not check_presence(tablename="indiz", column="name", filtername=indiz):
            result = dm.query(f"insert into indiz (name) values ('{indiz}');")

        indiz_id = dm.select(f"select indiz_id from indiz where name='{indiz}';")[0][0]
        result = dm.query(f"insert into data values(?, ?, ?);", val=(datum, indiz_id, data))
        print(result)

elif not (299 > res.status_code >= 200):
    raise ArithmeticError(f"Status Code: {res.status_code} occured!")

res = requests.delete(url, auth=HTTPBasicAuth(username, passwd))
print("Status Code from DELETE request:", res.status_code)
