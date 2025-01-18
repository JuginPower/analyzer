from datalayer import SqliteDatamanager
from datetime import datetime
import sqlite3
from pathlib import Path
import os
import pandas as pd
import settings


class BaseLoader(SqliteDatamanager):

    def __init__(self, filename = settings.sqlite_db_name):

        base_dir = Path(__file__).resolve().parent.parent
        database_file = os.path.join(base_dir, filename)

        super().__init__(database_file)

    def check_presence(self, tablename: str, column: str, filtername: str):
        result = self.select(f"select {column} from {tablename} where {column} like '%{filtername}%';") # Mit like verbessern
        if len(result) == 0:
            return False
        return True

    def upload(self, indiz_name: str, date: datetime, values: list):

        try:
            date = date.strftime("%d-%m-%Y")
            indiz_id = self.select(f"select indiz_id from indiz where name like '%{indiz_name}%';")[0][0]
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
            print(f"Something goes wrong for {indiz_name}!")
            print("Parameters are:", indiz_name, date, values)
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
                    actual_indiz: str = item.get("indiz")

                    if not self.check_presence(tablename="indiz", column="name", filtername=actual_indiz):
                        result = self.query(f"insert into indiz (name) values ('{actual_indiz}');")

                    if not old_indiz:
                        old_indiz = actual_indiz

                    if not old_date:
                        old_date = actual_date_obj

                    if old_date.day == actual_date_obj.day and old_indiz in item.get("indiz"):
                        numbers.append(item.get("data"))

                    elif not (old_date.day == actual_date_obj.day and old_indiz in item.get("indiz")):

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


class MainAnalyzer(BaseLoader):

    def __init__(self, indiz_id: int):
        super().__init__()

        self.indiz_id = indiz_id
        self.title: str = self.select(f"select name from indiz where indiz_id='{self.indiz_id}';")[0][0]

    def renew(self, indiz_id: int=None, *args) -> pd.DataFrame:

        """
        Macht ein neues Dataframe auf mit ggf. neuen Argumenten.

        :param indiz_id: Die Indiz Id für die Identifikation des Finanzinstruments.
        :param args: Zusätzliche Argumente, die die richtige Extraktion der Daten bewirken soll.
        :return: Gibt ein Dataframe zurück.
        """

        if indiz_id:
            self.indiz_id = indiz_id

        if len(args) > 0:
            return self.prepare_dataframe([arg for arg in args])

        return self.prepare_dataframe()

    def prepare_dataframe(self, *args) -> pd.DataFrame:

        """Bereitet und sortiert die Daten vor für die Analyse und gruppiert bei Bedarf"""

        df = pd.read_sql(f"select * from data where indiz_id='{self.indiz_id}';", con=self.init_conn())
        df["date"] = pd.to_datetime(df["date"], format="%d-%m-%Y")
        df = df.sort_values("date").reset_index(drop=True)

        if len(args) == 1:
            if isinstance(args[0], list):
                args = args[0]

        for arg in args:

            if arg == "year_month":
                # Wenn die Spalte year_month gebraucht wird
                df['year_month'] = df['date'].dt.to_period('M')

            if arg == "sift_out":
                df = self.sift_out(df)

        return df

    def sift_out(self, dataframe: pd.DataFrame, date_column: str = "year_month") -> pd.DataFrame:

        """
        Errechnet standardmäßig für jeden Monat die Höchs-, Tiefst- und Schlusskurse und gibt nur diese in einem neuen
        dataframe zurück.

        :param dataframe: Das zu gruppierende Dataframe.
        :param date_column: nach welcher Spalte gruppiert werden soll.
        :return: Gibt ein vor aggregiertes Dataframe zurück.
        """

        # Gruppen werden erstellt
        grouped = dataframe.groupby(date_column)
        results = []

        for name, group in grouped:
            # Für jede Gruppe wird eine Zeile erstellt mit den Höchst-, Tiefst- und Schlusswerten.
            highest_high = group['high'].max()
            lowest_low = group['low'].min()
            open_price = group.iloc[0]['open']
            close_price = group.iloc[-1]['close']

            # Ergebnisse hinzufügen.
            results.append({
                date_column: str(name),
                'high': highest_high,
                'low': lowest_low,
                'open': open_price,
                'close': close_price
            })
        # Ergebnisse in ein DataFrame umwandeln.
        summary_df = pd.DataFrame(results)
        return summary_df

    def get_last_month(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """
        Nimmt ein Dataframe des angefangenen Monats mit vorbereiteten Daten und füllt die Datensätze mit den restlichen
        Tagen auf.

        :param dataframe: Das Dataframe das aufgefüllt werden soll.
        :return: Gibt ein aggregiertes Dataframe zurück.
        """

        # Erstellung eines date range im letzten Monat bis zum letzten Tag der Aufzeichnung
        start_date = pd.to_datetime(dataframe.iloc[-1, 0] + "-01")
        end_date = start_date + pd.offsets.MonthEnd(0)

        # Erstelle einen erweiterten Dataframe
        extended_dates = pd.DataFrame({"date": pd.date_range(start=start_date, end=end_date, freq='B')})

        # Zusammenfassen der Daten des letzten und noch laufenden Monats (Ich brauche hier die täglichen Daten)
        df_orig = self.renew()
        df_last_month = df_orig[df_orig["date"] >= start_date].loc[:, "date": "close"]
        df_last_month.reset_index(drop=True, inplace=True)

        # Hier kommt das Merging des aktuellen vollständigen Monats mit den letzten Pivotlinien
        df_merged = self._merge_month(extended_dates, df_last_month, dataframe)

        return df_merged

    def _merge_month(self, extended_dates_dataframe: pd.DataFrame, last_month_dataframe: pd.DataFrame,
                     anal_dataframe: pd.DataFrame) -> pd.DataFrame: # Muss generalisiert werden
        """
        Fügt das ein Monats-Dataframe mit dem bis dato vorhandenen Monats-Dataframe zusammen und fügt das Zielwerkzeug
        der Analyze (anal_dataframe) hinzu.

        :param extended_dates_dataframe: Das auf den letzten Tag des Monats ausgeweitete noch leere Dataframe.
        :param last_month_dataframe: Das Dataframe mit den originellen Daten des laufenden Monats. 'self.renew()'
        :param anal_dataframe: Das vor aggregierte Zieldataframe, das es zu analysieren gibt.
        :return: Gibt ein aggregiertes Dataframe zurück.
        """

        df_merged = pd.merge(extended_dates_dataframe, last_month_dataframe, how="left", on="date").copy(deep=True)
        columns = [c for c in anal_dataframe.columns]

        for column in columns[columns.index('close')+1:]:
            df_merged[column] = [anal_dataframe.iloc[-1, columns.index(column)] for x in range(len(df_merged))]

        return df_merged


class PivotMaker(MainAnalyzer):

    """Noch nicht fertig, pivots.py als Beispiel nehmen"""

    def __init__(self, indiz_id: int):
        super().__init__(indiz_id)

    def prepare_dataframe(self, *args) -> pd.DataFrame:

        """Bereitet und sortiert die Daten vor für die Analyse und gruppiert bei Bedarf"""

        df = super().prepare_dataframe([arg for arg in args])

        for arg in args:

            if arg == "make_pivots":
                df = self.make_pivots(df)

        return df

    def make_pivots(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """Errechnet die Pivots von der letzten Zeitreihe für die aktuelle Zeitreihe"""

        df_copy = dataframe.copy(deep=True)
        df_copy["pivot"] = round((df_copy["high"].shift(1) + df_copy["low"].shift(1) + df_copy["close"].shift(1)) / 3,
                                 2)
        df_copy["R1"] = round(2 * df_copy["pivot"] - df_copy["low"].shift(1), 2)
        df_copy["R2"] = round(df_copy["pivot"] + (df_copy["high"].shift(1) - df_copy["low"].shift(1)), 2)
        df_copy["R3"] = round(df_copy["R1"] + (df_copy["high"].shift(1) - df_copy["low"].shift(1)), 2)

        df_copy["S1"] = round(2 * df_copy["pivot"] - df_copy["high"].shift(1), 2)
        df_copy["S2"] = round(df_copy["pivot"] - (df_copy["high"].shift(1) - df_copy["low"].shift(1)), 2)
        df_copy["S3"] = round(df_copy["S1"] - (df_copy["high"].shift(1) - df_copy["low"].shift(1)), 2)

        df_copy["P-MID-R1"] = round(df_copy["pivot"] + ((df_copy["R1"] - df_copy["pivot"]) / 2), 2)
        df_copy["R1-MID-R2"] = round(df_copy["R1"] + ((df_copy["R2"] - df_copy["R1"]) / 2), 2)
        df_copy["R2-MID-R3"] = round(df_copy["R2"] + ((df_copy["R3"] - df_copy["R2"]) / 2), 2)

        df_copy["P-MID-S1"] = round(df_copy["pivot"] - ((df_copy["pivot"] - df_copy["S1"]) / 2), 2)
        df_copy["S1-MID-S2"] = round(df_copy["S1"] - ((df_copy["S1"] - df_copy["S2"]) / 2), 2)
        df_copy["S2-MID-S3"] = round(df_copy["S2"] - ((df_copy["S2"] - df_copy["S3"]) / 2), 2)

        return df_copy

    def get_crossing_probability(self, dataframe: pd.DataFrame, year: int) -> dict: # Überarbeiten
        """
        Errechnet die Wahrscheinlichkeit der Kreuzung der Pivot-Linien anhand historischer Daten.

        :param dataframe: Das zu überprüfende Dataframe.
        :param year: Das Jahr ab wann die Berechnung beginnen soll.
        :return: gibt die Ergebnisse in einem Dictionary aus.

        """

        crosses = []
        probabilities = {}
        len_counter = 0
        columns = [c for c in dataframe.columns]

        for index, row in dataframe.iterrows():
            try:
                previous_row = dataframe.loc[int(index) - 1]
            except KeyError:
                continue
            else:

                for column in columns[columns.index('close') + 1:]:

                    if int(row.loc["year_month"].split("-")[0]) >= year:

                        if len_counter == 0:
                            len_counter = int(index)

                        if column[0] == "R" or column == "P-MID-R1":
                            if row["high"] > previous_row[column]:
                                crosses.append({"pivotname": column, "row": row})

                        elif column[0] == "S" or column == "P-MID-S1":
                            if row["low"] < previous_row[column]:
                                crosses.append({"pivotname": column, "row": row})

        for column in columns[columns.index('close') + 1:]:
            probability = round(
                ([d.get("pivotname") for d in crosses].count(column) / len(dataframe.iloc[len_counter:])) * 100, 3)
            probabilities.update({column: probability})

        return probabilities

