import csv
from helper import to_float
from datalayer import Datamanager
from pathlib import Path
import os


data_file = "data/DAX Historische Daten.csv"
indiz_id = 5
values = []

BASE_DIR = Path(__file__).resolve().parent.parent
database_file = os.path.join(BASE_DIR, "finance.sqlite3")
dm = Datamanager(database_file)

with open(data_file, "r") as df:
    data = csv.reader(df, delimiter=",")
    for line in data:
        try:
            float_number = to_float(line[1])
            date = line[0]
        except ValueError:
            continue
        else:
            values.append(tuple([date, indiz_id, float_number]))

result = dm.query("insert into data values (?, ?, ?);", values)
print("Rows inserted:", result)

if result > 0:
    os.remove(data_file)
