import csv
from funcs import to_float
from pathlib import Path
import os


BASE_DIR = Path(__file__).resolve().parent.parent
database_file = os.path.join(BASE_DIR, "finance.sqlite3")
data_file = "data/DAX Historische Daten-Daily.csv"
indiz_id = 5
values = []

with open(data_file, "r") as csvfile:
    reader = csv.DictReader(csvfile, delimiter=",")
    for row in reader:
        try:
            date_field = reader.fieldnames[0]
            open_field = reader.fieldnames[2]
            high_field = reader.fieldnames[3]
            low_field = reader.fieldnames[4]
            close_field = reader.fieldnames[1]

            item = {
                "date": row[date_field],
                "indiz_id": indiz_id,
                "open": to_float(row[open_field]),
                "high": to_float(row[high_field]),
                "low": to_float(row[low_field]),
                "close": to_float(row[close_field])}

        except ValueError as err:
            raise err
        except TypeError as err:
            raise err
        except IndexError as err:
            raise err

        else:
            values.append(item)


print(values)
