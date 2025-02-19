import pandas as pd
from classes import PivotMaker
from funcs import show_graph_objects, choose_id
from pathlib import Path
import os


BASE_DIR = Path(__file__).resolve().parent.parent
path_database = os.path.join(BASE_DIR, "finance.sqlite3")

while True:
    choosed_id = choose_id(path_database, "pivots")
    pm = PivotMaker(choosed_id)
    df_pivots: pd.DataFrame = pm.prepare_dataframe('year_month', 'sift_out', 'make_pivots')
    df_last_month: pd.DataFrame = pm.get_last_month(df_pivots)
    propabilities: dict = pm.get_crossing_probability(df_pivots, 2000)
    show_graph_objects(df_last_month, pm.title, propabilities)

    if input("Try another one in pivots theory? (n/y): ") in ('y', 'Y'):
        continue
    else:
        print("Programm stops now.")
        break
