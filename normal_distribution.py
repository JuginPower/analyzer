from funcs import show_graph_objects, get_iqrs, remove_outliers, get_gaus_normald, get_std, choose_id
from classes import MainAnalyzer
from copy import copy
from pathlib import Path
import os


BASE_DIR = Path(__file__).resolve().parent.parent
path_database = os.path.join(BASE_DIR, "finance.sqlite3")


while True:

    choosed_id = choose_id(path_database, "normal distributions")
    ma = MainAnalyzer(choosed_id)

    df_orig = ma.prepare_dataframe('year_month', 'sift_out')
    high_spreads = [h - o for h, o in zip(df_orig["high"], df_orig["open"])]  # May Scatterplott
    low_spreads = [o - l for o, l in zip(df_orig["open"], df_orig["low"])]

    iqrs_high_spreads = get_iqrs(high_spreads)
    iqrs_low_spreads = get_iqrs(low_spreads)

    high_spreads_cleaned = remove_outliers(copy(high_spreads), iqrs_high_spreads)  # May Scatterplott
    low_spreads_cleaned = remove_outliers(copy(low_spreads), iqrs_low_spreads)
    mean_high_cleaned = sum(high_spreads_cleaned) / len(high_spreads_cleaned)
    mean_low_cleaned = sum(low_spreads_cleaned) / len(low_spreads_cleaned)

    high_std = get_std(high_spreads_cleaned)
    low_std = get_std(low_spreads_cleaned)

    normalds_high = [get_gaus_normald(x, mean_high_cleaned, high_std) for x in high_spreads_cleaned]
    normalds_low = [get_gaus_normald(x, mean_low_cleaned, low_std) for x in low_spreads_cleaned]
    normalds_high.sort(key=lambda k: k["dense"])
    normalds_low.sort(key=lambda k: k["dense"])
    max_dense_high = normalds_high[-1]["x"]
    max_dense_low = normalds_low[-1]["x"]

    max_deviation_high = round(max_dense_high + high_std, 3)
    max_deviation_low = round(max_dense_low + low_std, 3)

    df_last_month = ma.get_last_month(df_orig)
    df_last_month["mean_high"] = round(df_orig.iloc[-1, 3] + max_dense_high, 3)
    df_last_month["mean_low"] = round(df_orig.iloc[-1, 3] - max_dense_low, 3)
    df_last_month["max_high"] = round(df_orig.iloc[-1, 3] + max_deviation_high, 3)
    df_last_month["max_low"] = round(df_orig.iloc[-1, 3] - max_deviation_low, 3)

    show_graph_objects(df_last_month, ma.title)

    if input("Try another one in normal distributions theory? (n/y): ") in ('y', 'Y'):
        continue
    else:
        print("Programm stops now.")
        break
