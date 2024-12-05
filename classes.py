from datalayer import Datamanager
from datetime import datetime
import sqlite3
from pathlib import Path
import os


class BaseLoader(Datamanager):

    def __init__(self):

        base_dir = Path(__file__).resolve().parent.parent
        database_file = os.path.join(base_dir, "finance.sqlite3")

        super().__init__(database_file)

    def check_presence(self, tablename: str, column: str, filtername: str):
        result = self.select(f"select {column} from {tablename} where {column}='{filtername}';") # Mit like verbessern
        if len(result) == 0:
            return False
        return True

    def upload(self, indiz_name: str, date: datetime, values: list):

        try:
            date = date.strftime("%d-%m-%Y")
            indiz_id = self.select(f"select indiz_id from indiz where name='{indiz_name}';")[0][0]
            result = self.select(f"select high, low, close from data where date='{date}' and indiz_id='{indiz_id}';")

            opening = values[0]
            high = max(values)
            low = min(values)
            close = values[-1]

            if len(result) > 0:
                # Überprüfung ob Daten für den jeweiligen Tag vorhanden sind.
                if high < result[0][0]:
                    high = result[0][0]

                if low > result[0][1]:
                    low = result[0][1]

                result = self.query(f"update data set high='{high}', low='{low}', close='{close}' where date='{date}' and indiz_id='{indiz_id}';")

            else:
                result = self.query("insert into data values (?, ?, ?, ?, ?, ?);",
                                    tuple([date, indiz_id, opening, high, low, close]))

        except (KeyError, sqlite3.Error) as err:
            raise err

        except IndexError as err:
            print(f"Empty list of data for {indiz_name}!")
            raise err

        else:
            return result


class ApiLoader(BaseLoader):

    def __init__(self):
        super().__init__()

    def upload(self, data_source: list):

        try:
            data_source.sort(key=lambda k: k["indiz"])
            data_source.sort(key=lambda k: datetime.strptime(k["datum"].split(",")[0], "%d-%m-%Y"))

        except (AttributeError, KeyError, IndexError) as err:
            raise err

        else:
            old_indiz = None
            old_date = None
            numbers = []

            try:
                for item in data_source:

                    actual_date_obj = datetime.strptime(item.get("datum"), "%d-%m-%Y, %H:%M:%S")
                    actual_indiz = item.get("indiz")

                    if not self.check_presence(tablename="indiz", column="name", filtername=actual_indiz):
                        result = self.query(f"insert into indiz (name) values ('{actual_indiz}');")

                    if not old_indiz:
                        old_indiz = actual_indiz

                    if not old_date:
                        old_date = actual_date_obj

                    if old_date.day == actual_date_obj.day and old_indiz == item.get("indiz"):
                        numbers.append(item.get("data"))

                    elif not (old_date.day == actual_date_obj.day and old_indiz == item.get("indiz")):

                        result = super().upload(old_indiz, old_date, numbers)
                        old_indiz = item.get("indiz")
                        old_date = actual_date_obj
                        numbers = []

                result = super().upload(old_indiz, old_date, numbers)

            except (KeyError, sqlite3.Error, IndexError) as err:
                raise err

            return result


class CsvLoader(BaseLoader):

    def __init__(self):
        super().__init__()

    def upload(self, data_source: list):

        try:
            result = self.query("insert into data values (?, ?, ?, ?, ?, ?);", data_source)

        except (sqlite3.Error, TypeError) as err:
            raise err

        else:
            return result