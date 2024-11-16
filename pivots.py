import pandas as pd
import matplotlib.pyplot as plt
from datalayer import Datamanager
from pathlib import Path
import os


BASE_DIR = Path(__file__).resolve().parent.parent
database_file = os.path.join(BASE_DIR, "finance.sqlite3")
dm = Datamanager(database_file)
df = pd.read_sql("select * from data;", con=dm.init_conn())
grouped = df.groupby('indiz_id')

calculated_dfs = {}

for indiz_id, group in grouped:
    group = group.sort_values("date").reset_index(drop=True)

    group["pivot"] = round((group["high"].shift(1) + group["low"].shift(1) + group["close"].shift(1)) / 3, 2)
    group["R1"] = round(2 * group["pivot"] - group["low"].shift(1), 2)
    group["R2"] = round(group["pivot"] + (group["high"].shift(1) - group["low"].shift(1)), 2)
    group["R3"] = round(group["R1"] + (group["high"].shift(1) - group["low"].shift(1)), 2)
    
    group["S1"] = round(2 * group["pivot"] - group["high"].shift(1), 2)
    group["S2"] = round(group["pivot"] - (group["high"].shift(1) - group["low"].shift(1)), 2)
    group["S3"] = round(group["S1"] - (group["high"].shift(1) - group["low"].shift(1)), 2)
    
    group["P-MID-R1"] = round(group["pivot"] + ((group["R1"] - group["pivot"]) / 2), 2)
    group["R1-MID-R2"] = round(group["R1"] + ((group["R2"] - group["R1"]) /2), 2)
    group["R2-MID-R3"] = round(group["R2"] + ((group["R3"] - group["R2"]) /2), 2)
    
    group["P-MID-S1"] = round(group["pivot"] - ((group["pivot"] - group["S1"]) / 2), 2)
    group["S1-MID-S2"] = round(group["S1"] - ((group["S1"] - group["S2"]) / 2), 2)
    group["S2-MID-S3"] = round(group["S2"] - ((group["S2"] - group["S3"]) / 2), 2)

    calculated_dfs[indiz_id] = group

for key, dataframe in calculated_dfs.items():

    crosses = [] # Nur für das jeweilige Dataframe
    probabilities = [] # Nur für das jeweilige Dataframe

    for index, row in dataframe.iterrows():
        try:
            previous_row = dataframe.loc[int(index) - 1]
        except KeyError:
            continue
        else:
            for column in dataframe.columns[6:]:

                if column[0] == "R" or column == "P-MID-R1":
                    if row["high"] > previous_row[column]:
                        crosses.append({"pivotname": column, "row": row})

                elif column[0] == "S" or column == "P-MID-S1":
                    if row["low"] < previous_row[column]:
                        crosses.append({"pivotname": column, "row": row})

    for column in df.columns[6:]: # Bevor ich das teste brauche ich mehr Daten!
        probability = round(([d.get("pivotname") for d in crosses].count(column) / len(df)) * 100, 3)
        probabilities.append({column:probability})

# Geil so kann ich die pivots für alle Indizien die ich runtergeladen bekomme überprüfen.
