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

# Erstellung eines date range im letzten Monat bis zum letzten Tag der Aufzeichnung
start_date = pd.to_datetime(df_pivots.iloc[-1,0] + "-01")
end_date = start_date + pd.offsets.MonthEnd(0)
date_range = pd.date_range(start=start_date, end=end_date, freq='D')

# Zusammenfassen der Daten des letzten und noch laufenden Monats
df_last_month = df[df["date"] >= start_date].loc[:, "date": "close"]
df_last_month.reset_index(drop=True)
df_last_month["pivot"] = [df_pivots.iloc[-1, 5] for x in range(len(df_last_month))]
df_last_month["P-MID-R1"] = [df_pivots.iloc[-1, 12] for x in range(len(df_last_month))]
df_last_month["R1"] = [df_pivots.iloc[-1, 6] for x in range(len(df_last_month))]
# Demnächst noch eine Linie mit dem Ausübungspreises der Option einzeichnen.
# Sollte 2 Drittel des Weges vom pivot bis zum P-MID-R1 betragen.
# Dann Plotten mit Candlesticks, dabei mplfinance recherchieren und Chat GPTs Antwort beachten.