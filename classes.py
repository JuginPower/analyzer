from datetime import datetime
import pandas as pd
from settings import mariadb_config, mariadb_string
import logging
from datalayer import MysqlConnectorManager
from sqlalchemy import create_engine
import random
from copy import copy


logger = logging.getLogger(__name__)
logging.basicConfig(filename="analyzer.log", encoding="utf-8", level=logging.ERROR,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d, %H:%M:%S')

class BaseLoader(MysqlConnectorManager):

    def __init__(self):

        super().__init__(mariadb_config)

    def check_presence(self, tablename: str, column: str, filtername: str):

        result = self.select(f"select {column} from {tablename} where {column} like '%{filtername}%';")

        if len(result) == 0:
            return False
        return True

    def upload(self, item_name: str, date: datetime, values: list):

        try:
            date: str = date.strftime("%Y-%m-%d")
            item_id = self.select(f"select item_id from items where name like '%{item_name}%';")[0][0]
            result = self.select(f"select high, low, close from stock_price where date='{date}' and item_id='{item_id}';")

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

                result = self.query(f"update stock_price set high='{high}', low='{low}', close='{close}' where date='{date}' and item_id='{item_id}';")

            else:
                result = self.query("insert into stock_price values (%s, %s, %s, %s, %s, %s);",
                                    tuple([item_id, date, opening, high, low, close]))

        except (IndexError, KeyError) as err:
            print(f"Something goes wrong for {item_name}!")
            print("Parameters are:", item_name, date, values)
            raise err

        else:
            return result


class ApiLoader(BaseLoader):

    def __init__(self):
        super().__init__()

    def upload(self, data_source: list):

        try:
            data_source.sort(key=lambda k: k["item"])
            data_source.sort(key=lambda k: datetime.strptime(k["datum"].split(",")[0], "%d-%m-%Y"))

        except (AttributeError, KeyError, IndexError) as err:
            raise err

        else:
            old_item = None
            old_date = None
            numbers = []

            try:
                for item in data_source:

                    actual_date_obj = datetime.strptime(item.get("datum"), "%d-%m-%Y, %H:%M:%S")
                    actual_item: str = item.get("item")

                    if not self.check_presence(tablename="items", column="name", filtername=actual_item):
                        result = self.query(f"insert into items (name) values (%s);", tuple(actual_item))

                    if not old_item:
                        old_item = actual_item

                    if not old_date:
                        old_date = actual_date_obj

                    if old_date.day == actual_date_obj.day and old_item in item.get("item"):
                        numbers.append(item.get("data"))

                    elif not (old_date.day == actual_date_obj.day and old_item in item.get("item")):

                        result = super().upload(old_item, old_date, numbers)
                        old_item = item.get("item")
                        old_date = actual_date_obj
                        numbers = []

                result = super().upload(old_item, old_date, numbers)

            except (KeyError, IndexError) as err:
                raise err

            return result


"""class CsvLoader(MysqlConnectorManager):

    def __init__(self):
        super().__init__(mariadb_config)

    def upload(self, item_id: int, data_file: str):

        values = []

        with open(data_file, "r") as csvfile:
            reader = csv.DictReader(csvfile, delimiter=",")
            for row in reader:
                try:
                    date_field = reader.fieldnames[0] # Selbsterkennung implementieren
                    open_field = reader.fieldnames[2]
                    high_field = reader.fieldnames[3]
                    low_field = reader.fieldnames[4]
                    close_field = reader.fieldnames[1]

                    item = (
                        row[date_field].replace(".", "-"),
                        item_id,
                        self.to_float(row[open_field]),
                        self.to_float(row[high_field]),
                        self.to_float(row[low_field]),
                        self.to_float(row[close_field])
                    )

                except (IndexError, TypeError, ValueError) as err:
                    raise err

                else:
                    values.append(item)

        try:
            result = self.query("insert into stock_price values (?, ?, ?, ?, ?, ?);", values)

        except TypeError as err:
            raise err

        else:
            return result"""


class MainAnalyzer(BaseLoader):

    def __init__(self, item_id: int):
        super().__init__()

        self.item_id = item_id
        self.title: str = self.select(f"select name from items where item_id='{self.item_id}';")[0][0]

    def renew(self, item_id: int=None, *args) -> pd.DataFrame:

        """
        Opens a new dataframe with new arguments if necessary.

        :param item_id: The index ID for identifying the financial instrument.
        :param args: Additional arguments to ensure correct data extraction.
        :return: Returns a new dataframe.
        """

        if item_id:
            self.item_id = item_id

        if len(args) > 0:
            return self.prepare_dataframe([arg for arg in args])

        return self.prepare_dataframe()

    def prepare_dataframe(self, *args) -> pd.DataFrame:

        """
        Prepares and sorts the data for analysis and groups if necessary

        :param args: It is important that the argument for sorting by month (M) or week (W) is specified first.
        """

        df = pd.read_sql(f"select * from stock_price where item_id='{self.item_id}';", con=create_engine(mariadb_string))
        df["date"] = pd.to_datetime(df["date"], format="%d-%m-%Y")
        df = df.sort_values("date").reset_index(drop=True)

        if len(args) == 1:
            if isinstance(args[0], list):
                args = args[0]

        for arg in args:

            if arg == "M":
                # Wenn die Spalte year_month gebraucht wird
                df['year_month'] = df['date'].dt.to_period(arg)

            if arg == "W":
                df['weekly'] = df['date'].dt.to_period(arg)

            if arg == "sift_out":
                df = self.sift_out(df, df.columns[-1])

        return df

    def sift_out(self, dataframe: pd.DataFrame, date_column: str) -> pd.DataFrame:

        """
        Calculates the high, low, and close prices for the grouped column and returns only these in a new dataframe.

        :param dataframe: The dataframe to be grouped.
        :param date_column: Nach welcher Spalte gruppiert werden soll.
        :return: Returns a pre-aggregated dataframe.
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

    def to_float(self, str_number: str, absolut=False) -> float:

        """
        Formats a string into a floating point number.

        :param str_number: The string to be formatted.
        :param absolut: Determines whether the floating point number should represent an absolute value or not.
        :return: Returns the completely transformed floating point number.
        """

        result = None

        try:
            if len(str_number) >= 7:
                result = str_number.replace(".", "_").replace(",", ".")

            elif len(str_number) < 7:
                result = str_number.replace(",", ".")

            if absolut:
                result = abs(float(result))
            elif not absolut:
                result = float(result)

        except ValueError as err:
            raise err

        except TypeError as err:
            raise err

        return result


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


class KMeansClusterMain:

    def __init__(self, n_clusters: int):

        self.clusters = n_clusters
        self._labels = None
        self._centroids = None

    def get_centroids(self):

        """
        Getter for the centroids which are computed

        :return self._centroids: The new centroids
        """

        return  self._centroids

    def get_labels(self):

        """
        Getter for the clusters

        :return self._labels: The clusters
        """

        return self._labels

    def fit(self, datapoints: list):

        """
        Begins the process where the reassignment of the centroids continued till the assignment of the clusters for
        each datapoint ends

        :param datapoints: one dimensional list of numerical datapoints
        """

        centroids = self._place_centroids(datapoints)
        ordered_clusters = self._assign_nearest_centroid(datapoints, centroids)
        new_centroids = self._replace_centroids(datapoints, ordered_clusters, centroids)
        new_ordered_clusters = self._assign_nearest_centroid(datapoints, new_centroids)

        while ordered_clusters != new_ordered_clusters:

            # Necessary because of call by object behaviour from python its safely make independent copies and reassign
            ordered_clusters = copy(new_ordered_clusters)
            centroids = copy(new_centroids)

            new_centroids = self._replace_centroids(datapoints, ordered_clusters, centroids)
            new_ordered_clusters = self._assign_nearest_centroid(datapoints, new_centroids)

        self._labels = new_ordered_clusters
        self._centroids = centroids

    def _place_centroids(self, datapoints: list) -> dict:

        """
        Choose random centroids in the pandas series

        :param datapoints: A pandas Series with numerical values

        :return dict: A dictionary with the centroids
        """

        result = {}

        for n in range(self.clusters):
            centroid = random.choice(datapoints)
            result.update({"c" + str(n): centroid})

        return result

    def _assign_nearest_centroid(self, datapoints: list, centroids: dict) -> list:

        """
        Find the nearest centroid for any datapoint and assign this datapoint to this centroid

        :param datapoints: A list wich is assumed to be the whole dataset.
        :param centroids: A dictionary with the given centroids.

        :return: An ordered list with the choosen centroids.
        """

        ordered_centroids = []

        for dp in datapoints:

            distances = []
            names = []

            for cent in centroids.items():
                distances.append(abs(dp - cent[1]))
                names.append(cent[0])

            index_min_distance = distances.index(min(distances))
            ordered_centroids.append(names[index_min_distance])

        return ordered_centroids

    def _replace_centroids(self, datapoints: list, ordered_clusters: list, centroids: dict):

        """
        Replace the centroids with new values.

        :param datapoints: original datapoints
        :param ordered_clusters: An ordered list of centroids assigned before to the datapoints
        :param centroids: the centroids with the old values

        :return: A dictionary with the old centroid keys but new centroid values
        """

        new_centroids = {}

        for cent_key in centroids.keys():
            cluster = [dtp for dtp, ordc in zip(datapoints, ordered_clusters) if ordc == cent_key]
            new_centroid = sum(cluster) / len(cluster)
            new_centroids.update({cent_key: new_centroid})

        return new_centroids


class HiddenMarkovModelMain:

    def __init__(self, states: list):

        self.states = states

    def fit(self):

        pass

    def _get_initial_p(self):

        """
        It gets the initial probabilities for the different states
        """

        pass
