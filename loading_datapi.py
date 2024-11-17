import requests
from requests.auth import HTTPBasicAuth
from datalayer import Datamanager
from pathlib import Path
import os
from datetime import datetime


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
    data_source.sort(key=lambda k: k.get("indiz"))
    data_source.sort(key=lambda k: datetime.strptime(k.get("datum").split(",")[0], "%d-%m-%Y"))
    old_indiz = None
    old_date = None
    numbers = []
    for item in data_source:

        actual_date_obj = datetime.strptime(item.get("datum"), "%d-%m-%Y, %H:%M:%S")
        actual_indiz = item.get("indiz")

        if not check_presence(tablename="indiz", column="name", filtername=actual_indiz):
            result = dm.query(f"insert into indiz (name) values ('{actual_indiz}');")
            print("New Indiz inserted into indiz:", actual_indiz)

        if not old_indiz:
            old_indiz = actual_indiz

        if not old_date:
            old_date = actual_date_obj

        if old_date.day == actual_date_obj.day and isinstance(old_indiz, str) and old_indiz == item.get("indiz"):
            numbers.append(item.get("data"))

        else:
            indiz_id = dm.select(f"select indiz_id from indiz where name='{old_indiz}';")[0][0]
            result = dm.query("insert into data values (?, ?, ?, ?, ?, ?);", tuple([old_date.strftime("%d-%m-%Y"), indiz_id, numbers[0], max(numbers), min(numbers), numbers[-1]]))
            old_indiz = item.get("indiz")
            old_date = actual_date_obj
            numbers = []
            print(result)

elif not (299 > res.status_code >= 200):
    raise ArithmeticError(f"Status Code: {res.status_code} occured!")

res = requests.delete(url, auth=HTTPBasicAuth(username, passwd))
print("Status Code from DELETE request:", res.status_code)
