import pandas as pd
from classes import BaseLoader
from funcs import prepare_dataframe, show_graph_objects


loader = BaseLoader()
indiz_id = 33
title = loader.select(f"select name from indiz where indiz_id='{indiz_id}';")[0][0]
ma_pivot = "R1"
year = 2014

def make_pivots(df: pd.DataFrame) -> pd.DataFrame:

    """Errechnet die Pivots von der letzten Zeitreihe für die aktuelle Zeitreihe"""

    df_copy = df.copy(deep=True)
    df_copy["pivot"] = round((df_copy["high"].shift(1) + df_copy["low"].shift(1) + df_copy["close"].shift(1)) / 3, 2)
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


def get_crossing_probability(df: pd.DataFrame, starting_pivot_column: int, year: int) -> dict:

    """Errechnet die Wahrscheinlichkeit der Kreuzung der Pivot-Linien anhand historischer Daten"""

    crosses = []
    probabilities = {}
    len_counter = 0

    for index, row in df.iterrows():
        try:
            previous_row = df.loc[int(index) - 1]
        except KeyError:
            continue
        else:
            for column in df.columns[starting_pivot_column:]:

                if int(row.loc["year_month"].split("-")[0]) >= year:

                    if len_counter == 0:
                        len_counter = int(index)

                    if column[0] == "R" or column == "P-MID-R1":
                        if row["high"] > previous_row[column]:
                            crosses.append({"pivotname": column, "row": row})

                    elif column[0] == "S" or column == "P-MID-S1":
                        if row["low"] < previous_row[column]:
                            crosses.append({"pivotname": column, "row": row})


    for column in df.columns[starting_pivot_column:]:
        probability = round(([d.get("pivotname") for d in crosses].count(column) / len(df.iloc[len_counter:])) * 100, 3)
        probabilities.update({column:probability})

    return probabilities


def merge_pivots(extended_dates_dataframe: pd.DataFrame, last_month_dataframe: pd.DataFrame, pivots_dataframe: pd.DataFrame, fav_pivot=ma_pivot, starting_column=5):

    """Nimmt ein Dataframe vom aktuellen vollständigen Monat und merged diesen mit den letzten pivots für diesen Monat."""
     
    df_merged = pd.merge(extended_dates_dataframe, last_month_dataframe, how="left", on="date").copy(deep=True)
    pivot_columns = [c for c in pivots_dataframe.columns]

    for column in pivot_columns[starting_column:]:

        df_merged[column] = [pivots_dataframe.iloc[-1, pivot_columns.index(column)] for x in range(len(df_merged))]

    if "R" in fav_pivot:
        df_merged["Strike"] = df_merged["pivot"] + ((df_merged[fav_pivot] - df_merged["pivot"]) / 3 * 2)
    elif "S" in fav_pivot:
        df_merged["Strike"] = df_merged["pivot"] - ((df_merged["pivot"] - df_merged[fav_pivot]) / 3 * 2)

    return df_merged


df_orig = prepare_dataframe(indiz_id)
df_prepared = prepare_dataframe(indiz_id, 'year_month', 'sift_out')
df_pivots = make_pivots(df_prepared)
probabilities = get_crossing_probability(df_pivots, 5, year)

# Erstellung eines date range im letzten Monat bis zum letzten Tag der Aufzeichnung
start_date = pd.to_datetime(df_pivots.iloc[-1,0] + "-01")
end_date = start_date + pd.offsets.MonthEnd(0)

# Erstelle einen erweiterten Dataframe
extended_dates = pd.DataFrame({"date": pd.date_range(start=start_date, end=end_date, freq='B')})

# Zusammenfassen der Daten des letzten und noch laufenden Monats
df_last_month = df_orig[df_orig["date"] >= start_date].loc[:, "date": "close"]
df_last_month.reset_index(drop=True, inplace=True) # Funktioniert iwie nicht

# Hier kommt das Merging des aktuellen vollständigen Monats mit den letzten Pivotlinien
df_merged = merge_pivots(extended_dates, df_last_month, df_pivots)

# Nutzung des Frameworks plotly für den Candle-Stick Chart
show_graph_objects(df_merged, title, probabilities)