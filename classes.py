from datetime import datetime
from sqlalchemy import create_engine
from copy import copy
import pandas as pd
import logging
import random
import math
from funcs import sort_dict_values
from datalayer import MysqlDataManager


logger = logging.getLogger(__name__)
logging.basicConfig(filename="classes.log", encoding="utf-8", level=logging.ERROR,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d, %H:%M:%S')


class BaseLoader(MysqlDataManager):

    def __init__(self, db_config: dict):
        super().__init__(db_config)

    def check_presence(self, tablename: str, column: str, filtername: str):

        result = self.select(f"select {column} from {tablename} where {column} like '%{filtername}%';")

        if len(result) == 0:
            return False
        return True

    def upload(self, data_source: list[dict]) -> int:

        """
        Uploads the data with the help of datamanager to a database.

        :param data_source: A list of dictionary items should match the database schema.
        :type data_source: list[dict]
        :raise: Any possible Exception. It Will be logged and raised.
        :return: number of affected rows in the database
        :rtype: int
        """

        inserted_price_rows = 0

        try:
            data_source.sort(key=lambda k: k["symbol"])
            data_source.sort(key=lambda k: datetime.strptime(k["datum"].split(",")[0], "%Y-%m-%d"))

            for item in data_source:

                actual_date_obj = datetime.strptime(item.get("datum"), "%Y-%m-%d")
                actual_item: str = item.get("symbol")

                opening = float(item.get("open"))
                high = float(item.get("high"))
                low = float(item.get("low"))
                closing = float(item.get("price"))
                values = tuple([actual_item, actual_date_obj.strftime("%Y-%m-%d"), opening, high, low, closing])

                # Not known symbols
                if not self.check_presence(tablename="stocks", column="symbol", filtername=actual_item):
                    inserted_symbols = self.query(f"insert into stocks (symbol) values (%s);", tuple([actual_item]))
                    message = "Item {} inserted.\nAffected rows: {}".format(actual_item, inserted_symbols)
                    print(message)

                inserted_price_rows += self.query("insert into stock_price values (%s, %s, %s, %s, %s, %s);", values)

        except Exception as err:
            logger.error("Something goes wrong in BaseLoader.upload: %s", err)
            raise err

        else:
            return inserted_price_rows

    def choose_id(self) -> str | None:
        """
        This method should simply explain the user which symbol or name stands for which index and return the symbol.
        The user can select the index in order by symbol.

        :return: the symbol for further evaluation or None
        :rtype: str | None
        """

        stocks = [dict(symbol=stock[0], name=stock[1]) for stock in self.select("select * from stocks;")]
        symbols = []
        return_symbol = None

        print(f"Please choose the symbol from the index which data should be analysed.")

        for index_row in stocks:
            symbol = index_row.get('symbol')
            name = index_row.get('name')
            symbols.append(symbol)
            print(f"symbol {symbol}: {name}")

        print("You can typ 'q' to quit.")
        while True:

            choosed_symbol = input("symbol: ")

            if choosed_symbol in symbols:
                return_symbol = choosed_symbol
                break
            elif choosed_symbol in ("Q", "q"):
                break
            else:
                print(f"There is no {choosed_symbol} in the database, please try another!")
                continue

        return return_symbol

    def get_stock_name(self, symbol: str):

        result = self.select(f"select name from stocks where symbol='{symbol}';")
        return result[0][0]


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

        :return list: An ordered list with the choosen centroids.
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

        :return dict: A dictionary with the old centroid keys but new centroid values
        """

        new_centroids = {}

        for cent_key in centroids.keys():
            cluster = [dtp for dtp, ordc in zip(datapoints, ordered_clusters) if ordc == cent_key]
            new_centroid = sum(cluster) / len(cluster)
            new_centroids.update({cent_key: new_centroid})

        return new_centroids


if __name__=='__main__':

    pass