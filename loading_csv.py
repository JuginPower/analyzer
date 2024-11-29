import csv
from funcs import to_float
from classes import CsvLoader
import sqlite3


data_file = "data/BASF11 Historische Daten.csv"
indiz_id = 26
values = []
loader = CsvLoader()

with open(data_file, "r") as csvfile:
    reader = csv.DictReader(csvfile, delimiter=",")
    for row in reader:
        try:
            date_field = reader.fieldnames[0]
            open_field = reader.fieldnames[2]
            high_field = reader.fieldnames[3]
            low_field = reader.fieldnames[4]
            close_field = reader.fieldnames[1]

            item = { # Es soll ein tuple sein kein dictionary mit Namen da AdvancedLoader gelöscht
                "date": row[date_field],
                "indiz_id": indiz_id,
                "open": to_float(row[open_field]),
                "high": to_float(row[high_field]),
                "low": to_float(row[low_field]),
                "close": to_float(row[close_field])}

        except (IndexError, TypeError, ValueError) as err:
            raise err

        else:
            values.append(item)

try:
    result = loader.upload(values)

except sqlite3.Error as err:
    raise err

else:
    print("Result from upload from csv:", result)

