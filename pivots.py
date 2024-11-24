import pandas as pd
import matplotlib.pyplot as plt
from classes import AdvancedLoader


def sift_out(df: pd.DataFrame, date_column: str = "year_month"):

    grouped = df.groupby(date_column)
    results = []

    for name, group in grouped: # name ist der index bzw. date_column = 'year_month'
        # Berechnungen innerhalb der Gruppen
        highest_high = group['high'].max()
        lowest_low = group['low'].min()
        open_price = group.iloc[0]['open']
        close_price = group.iloc[-1]['close']

        # Ergebnisse hinzufügen
        results.append({
            date_column: str(name),
            'high': highest_high,
            'low': lowest_low,
            'open': open_price,
            'close': close_price
        })
    # Ergebnisse in ein DataFrame umwandeln
    summary_df = pd.DataFrame(results)
    return summary_df


def make_pivots(df: pd.DataFrame): # Verbessern, es muss neues df raus kommen
    
    df["pivot"] = round((df["high"].shift(1) + df["low"].shift(1) + df["close"].shift(1)) / 3, 2)
    df["R1"] = round(2 * df["pivot"] - df["low"].shift(1), 2)
    df["R2"] = round(df["pivot"] + (df["high"].shift(1) - df["low"].shift(1)), 2)
    df["R3"] = round(df["R1"] + (df["high"].shift(1) - df["low"].shift(1)), 2)

    df["S1"] = round(2 * df["pivot"] - df["high"].shift(1), 2)
    df["S2"] = round(df["pivot"] - (df["high"].shift(1) - df["low"].shift(1)), 2)
    df["S3"] = round(df["S1"] - (df["high"].shift(1) - df["low"].shift(1)), 2)

    df["P-MID-R1"] = round(df["pivot"] + ((df["R1"] - df["pivot"]) / 2), 2)
    df["R1-MID-R2"] = round(df["R1"] + ((df["R2"] - df["R1"]) / 2), 2)
    df["R2-MID-R3"] = round(df["R2"] + ((df["R3"] - df["R2"]) / 2), 2)

    df["P-MID-S1"] = round(df["pivot"] - ((df["pivot"] - df["S1"]) / 2), 2)
    df["S1-MID-S2"] = round(df["S1"] - ((df["S1"] - df["S2"]) / 2), 2)
    df["S2-MID-S3"] = round(df["S2"] - ((df["S2"] - df["S3"]) / 2), 2)

    return df


def get_crossing_probability(df: pd.DataFrame, starting_pivot_column: int):

    crosses = []
    probabilities = []

    for index, row in df.iterrows():
        try:
            previous_row = df.loc[int(index) - 1]
        except KeyError:
            continue
        else:
            for column in df.columns[starting_pivot_column:]:

                if column[0] == "R" or column == "P-MID-R1":
                    if row["high"] > previous_row[column]:
                        crosses.append({"pivotname": column, "row": row})

                elif column[0] == "S" or column == "P-MID-S1":
                    if row["low"] < previous_row[column]:
                        crosses.append({"pivotname": column, "row": row})

    for column in df.columns[starting_pivot_column:]:
        probability = round(([d.get("pivotname") for d in crosses].count(column) / len(df)) * 100, 3)
        probabilities.append({column:probability})

    return probabilities


loader = AdvancedLoader()
indiz_id = 5
df = pd.read_sql(f"select * from data where indiz_id='{indiz_id}';", con=loader.init_conn())
df["date"] = pd.to_datetime(df["date"], format="%d-%m-%Y")
df = df.sort_values("date").reset_index(drop=True)
df['year_month'] = df['date'].dt.to_period('M')

df_sifted = sift_out(df)
df_pivots = make_pivots(df_sifted)
probabilities = get_crossing_probability(df_pivots, 5)
print(probabilities)

# Geil so kann ich die pivots für alle Indizien die ich runtergeladen bekomme überprüfen.
