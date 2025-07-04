from datetime import datetime
from settings import mariadb_config, mariadb_string
from sqlalchemy import create_engine
from copy import copy
import pandas as pd
import logging
import random
import math
import sqlite3
import mysql.connector
from time import sleep
from funcs import sort_dict_values


logger = logging.getLogger(__name__)
logging.basicConfig(filename="analyzer.log", encoding="utf-8", level=logging.ERROR,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d, %H:%M:%S')

sql_script = """
"""

class MysqlConnectorManager:

    def __init__(self, config: dict):

        self.config = config

    def init_conn(self, attempts=3, delay=2):

        """
        Initialize the connection with my mariadb database.

        :param attempts: amount of attempts
        :param delay: waiting seconds for trying to reconnect
        """

        attempt = 1
        # Implement a reconnection routine
        while attempt < attempts + 1:
            try:
                return mysql.connector.connect(**self.config)
            except (mysql.connector.Error, IOError) as err:
                if attempts is attempt:
                    # Attempts to reconnect failed; returning None
                    logger.error("Failed to connect, exiting without a connection: %s", err)
                    return None
                logger.info(
                    "Connection failed: %s. Retrying (%d/%d)...",
                    err,
                    attempt,
                    attempts - 1,
                )
                # progressive reconnect delay
                sleep(delay ** attempt)
                attempt += 1
        return None

    def select(self, sqlstring):

        mydb = self.init_conn()
        cursor = mydb.cursor()

        try:
            cursor.execute(sqlstring)
        except (mysql.connector.Error, IOError) as err:
            raise err

        result = cursor.fetchall()
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

        except (mysql.connector.Error, IOError) as err:
            raise err

        mydb.commit()
        mydb.close()
        return mycursor.rowcount


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

    def select_pragma_info(self, tablename: str):

        return self.select(f"select * from pragma_table_info('{tablename}');")

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


class BaseLoader(MysqlConnectorManager):

    def __init__(self):

        super().__init__(mariadb_config)

    def check_presence(self, tablename: str, column: str, filtername: str):

        result = self.select(f"select {column} from {tablename} where {column} like '%{filtername}%';")

        if len(result) == 0:
            return False
        return True

    def upload(self, item_name: str, date: datetime, values: list): # Überarbeiten

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

    def choose_id(self, theory_name: str) -> int:
        """
        This method should simply explain the user which id stands for which index

        :theory_name: Kind of theory name for right naming purposes

        :return: the id for further evaluation
        """

        indizes = [dict(indiz_id=indiz[0], indiz_name=indiz[1]) for indiz in self.select("select * from items;")]
        indiz_ids = []
        choosed_id = None

        print(f"Please choose the indiz_id for the indiz to analyse it with the {theory_name} theory:\n")

        for indiz_row in indizes:
            indiz_id = indiz_row.get('indiz_id')
            indiz_ids.append(indiz_id)
            print(f"id {indiz_id}: {indiz_row.get('indiz_name')}")

        print()
        while True:
            try:
                choosed_id = int(input("id: "))
            except ValueError:
                print(choosed_id, "is not an integer!")
            else:
                if choosed_id in indiz_ids:
                    break
                else:
                    print(f"There is no {choosed_id} in the database, please try another!")
                    continue

        return choosed_id


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
        self.labels = None
        self.centroids = None

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

        self.labels = new_ordered_clusters
        self.centroids = centroids

    def _place_centroids(self, datapoints: list) -> dict:

        """
        Choose random centroids in the list

        :param datapoints: A list with numerical values

        :return dict: A dictionary with the centroids
        """

        result = {}

        for n in range(self.clusters):
            centroid = random.choice(datapoints)
            result.update({n: centroid})

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

# In the future maybe solve the problem with the Log zero replacement
class HiddenMarkovModelMain:

    def __init__(self, states: list):

        self.states = ["c" + str(st) for st in states]
        self.states_p = []
        self.emission_p = {}
        self.initial_p = {}
        self.transition_p = {}

    def fit(self, datapoints: list, window: int):

        """
        Begins the process of Hidden Markov Model
        """

        def get_direction(number: int | float) -> str:
            """
            Returns a string depended on the parameter

            :param number: A float or integer above or under 0
            :return str: h or l
            """

            if number > 0:
                return "h"
            return "l"

        amount_states = len(self.states)

        for st in set(self.states):
            self.initial_p.update({st: self.states.count(st) / amount_states})
            self._compute_emission_p(st, datapoints)

        self._compute_transition_p()

        direction = get_direction(datapoints[0])

        # First Day state probability
        row_p = [{key: math.log(self.emission_p[key + direction]) + math.log(init_state_p)}
                 for key, init_state_p in self.initial_p.items()]
        self.states_p.append(tuple(row_p))
        counter = 0
        for i in range(1, len(datapoints)):
            direction = get_direction(datapoints[i])
            row_p = []
            # Here comes the Viterbi algorithm
            if counter == window:
                row_p = [{key: math.log(self.emission_p[key + direction]) + math.log(init_state_p)}
                         for key, init_state_p in self.initial_p.items()]
                counter = 0
            else:
                yesterday_items = self.states_p[i-1]
                for item in yesterday_items:
                    today_state_choices_p = []

                    for key in self.initial_p.keys():
                        if key in item.keys():
                            yest_state_p = item.get(key)
                            for t_key in self.transition_p.keys():
                                if key == t_key[:2]:
                                    today_state_p = yest_state_p + math.log(self.transition_p.get(t_key)) + math.log(self.emission_p.get(key+direction))
                                    today_state_choices_p.append({key: today_state_p})

                    today_state_choices_p.sort(key=sort_dict_values, reverse=True)
                    row_p.append(today_state_choices_p[0])

            self.states_p.append(tuple(row_p))
            counter += 1

    def _compute_transition_p(self):

        """
        For computing the probability to each combination of transition from one state to another
        """
        unique_states = [k for k in self.initial_p.keys()]
        states_copy: list = copy(self.states)

        for st in unique_states:

            for other_st in unique_states:

                self.transition_p.update({st + "_" + other_st: 0})

        while states_copy:

            current_state = states_copy.pop(0)

            if len(states_copy) == 0:
                break
            else:
                next_state = states_copy.pop(0)
                transition_key = current_state + "_" + next_state
                self.transition_p[transition_key] += 1

        for st in unique_states:
            # The total variable represents the total amount auf transitions for each unique state
            total = 0

            for k, v in self.transition_p.items():

                if st == k[0:2]:
                    total += v

            for k, v in self.transition_p.items():

                if st == k[0:2]:
                    self.transition_p[k] /= total

    def _compute_emission_p(self, actual_state: str, datapoints: list):

        """
        Gets the probability of two possible emissions 'h' and 'l' in any state

        :param actual_state: the actual given state in a row
        :param datapoints: the population of all floats around number 0 used to determine the emission 'h' or 'l'
        """
        state_emissions = {actual_state + "h": 0, actual_state + "l": 0}
        total_actual_st = 0

        for dtp, state in zip(datapoints, self.states):

            if dtp > 0 and state == actual_state:
                state_emissions[actual_state + "h"] += 1
                total_actual_st += 1

            elif dtp < 0:
                state_emissions[actual_state + "l"] += 1
                total_actual_st += 1

        # Laplace Smoothing
        total_actual_st += 2
        state_emissions[actual_state + "h"] += 1
        state_emissions[actual_state + "l"] += 1

        for k in state_emissions:
            state_emissions[k] /= total_actual_st

        self.emission_p.update(state_emissions)


class TrendColorIndicator:

    """
    Main goal of this class of objects is to serve as a wrapper class for the other implementations of the algorithms.
    """

    def __init__(self, n_clusters: int):

        self._clusters = n_clusters
        self._kmeans = KMeansClusterMain(self._clusters)
        self._hmm = None

    def fit(self, datapoints: list, window: int=20):

        self._kmeans = KMeansClusterMain(self._clusters)
        self._kmeans.fit(datapoints)
        self._hmm = HiddenMarkovModelMain(self._kmeans.labels)
        self._hmm.fit(datapoints, window)

    def set_cluster(self, new_cluster: int):
        """
        Setter of the attribute _clusters for trying another case.

        :param new_cluster: An integer which tells how many regimes or clusters to compute.
        """

        self._clusters = new_cluster

    def get_states(self):

        """
        Getter for the original states or clusters.

        :return: A list with the states
        """

        try:
            return self._hmm.states
        except AttributeError:
            return self._kmeans.labels

    def get_states_probabilities(self, treaded=True) -> list:

        """
        Getter for the computed probabilities for the states from the HiddenMarkovModel algorithm.

        :param treaded: Boolean flag for treading the probs or not before returning
        :return: The computed probabilities for the states
        """

        winners = []
        if treaded:
            for tp, st in zip(self._hmm.states_p, self._hmm.states):

                tp_l = list(tp)
                tp_l.sort(key=sort_dict_values, reverse=True)

                # Get the current largest prob for the state
                state_largest_p = list(tp_l[0].keys())[0]
                winners.append(state_largest_p)

            return winners

        else:
            return self._hmm.states_p

    def get_initial_probabilities(self):

        """
        Getter for the computed initial probabilities for the states from the HiddenMarkovModel algorithm.

        :return: The computed initial probabilities for the states.
        """

        return self._hmm.initial_p

    def get_emission_probabilities(self):

        """
        Getter for the computed emission probabilities for the states from the HiddenMarkovModel-Algorithm.

        :return: The computed probabilities for the states
        """

        return self._hmm.emission_p

    def get_transition_probabilities(self):

        """
        Getter for the computed transition probabilities for the states from the HiddenMarkovModel algorithm.

        :return: The computed probabilities for the states
        """

        return self._hmm.transition_p

    def get_centroids(self):

        """
        Getter for the centroids which are computed by the KMeans-Clustering-Algorithm

        :return: The centroids which were computed by the KMeans-Clustering-Algorithm
        """

        return  self._kmeans.centroids


if __name__=='__main__':

    engine = create_engine(mariadb_string)
    item_id = 5
    sql_query = """
    select 
        `date`, 
        `close` 
    from stock_price 
        where item_id={item_id}
    order by `date` asc;
    """.format(item_id=item_id)

    # Compute percentage change
    df_ndafi = pd.read_sql(sql_query, con=engine)
    df_ndafi["date"] = pd.to_datetime(df_ndafi["date"], yearfirst=True)
    df_ndafi["perc_change"] = df_ndafi["close"].pct_change()

    # Also drop the first row because of pct_change
    df_ndafi.dropna(inplace=True)

    datapoints = df_ndafi["perc_change"].to_list()

    tdc = TrendColorIndicator(3)
    tdc.fit(datapoints, 20)
    df_ndafi["cluster"] = tdc.get_states_probabilities()
    df_ndafi_copy = df_ndafi.copy()
    print(df_ndafi.info())
    print(df_ndafi.head())
    print(df_ndafi["cluster"].value_counts())
