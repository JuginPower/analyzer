from datalayer import Datamanager
from datetime import datetime
import sqlite3


class BaseLoader(Datamanager):

    def __init__(self, database_name: str):
        super().__init__(database_name)

    def check_presence(self, tablename: str, column: str, filtername: str):
        result = self.select(f"select {column} from {tablename} where {column}='{filtername}';")
        if len(result) == 0:
            return False
        return True

    def upload(self, indiz_name: str, date: datetime, values: list) -> bool:

        if len(values) < 95: # Wenn zu wenig Values dann unvollständiger Tag.
            return False

        try:
            indiz_id = self.select(f"select indiz_id from indiz where name='{indiz_name}';")[0][0]
            result = self.query("insert into data values (?, ?, ?, ?, ?, ?);", tuple(
                [date.strftime("%d-%m-%Y"), indiz_id, values[0], max(values), min(values), values[-1]]))

        except (IndexError, sqlite3.Error) as err:
            raise err

        else:
            return True

class ApiLoader(BaseLoader):

    def __init__(self, database_name):
        super().__init__(database_name)

    def upload(self, data_source: list) -> bool:

        try:
            data_source.sort(key=lambda k: k["indiz"])
            data_source.sort(key=lambda k: datetime.strptime(k["datum"].split(",")[0], "%d-%m-%Y"))

        except (AttributeError, KeyError, IndexError) as err:
            raise err

        else:
            old_indiz = None
            old_date = None
            numbers = []

            for item in data_source:

                actual_date_obj = datetime.strptime(item.get("datum"), "%d-%m-%Y, %H:%M:%S")
                actual_indiz = item.get("indiz")

                if not self.check_presence(tablename="indiz", column="name", filtername=actual_indiz):
                    result = self.query(f"insert into indiz (name) values ('{actual_indiz}');")

                if not old_indiz:
                    old_indiz = actual_indiz

                if not old_date:
                    old_date = actual_date_obj

                if old_date.day == actual_date_obj.day and isinstance(old_indiz, str) and old_indiz == item.get("indiz"):
                    numbers.append(item.get("data"))

                else:
                    result = super().upload(old_indiz, old_date, numbers)
                    old_indiz = item.get("indiz")
                    old_date = actual_date_obj
                    numbers = []

            return True

class AdvancedLoader(ApiLoader):

    def __init__(self, database_name):
        super().__init__(database_name)

    def upload(self, data_source: list) -> bool:
        """Hier muss ich eine Exception suchen oder machen um nach super weiter leiten zu können!"""

        try:
            for item in data_source:
                date: str = datetime.strptime(item["date"], "%d.%m.%Y").strftime("%d-%m-%Y")
                indiz_id = item["indiz_id"]
                open = item["open"]
                high = item["high"]
                low = item["low"]
                close = item["close"]
                result = self.query("insert into data values (?, ?, ?, ?, ?, ?);",
                                    tuple([date, indiz_id, open, high, low, close]))

        except KeyError:
            super().upload(data_source)

        else:
            return True
