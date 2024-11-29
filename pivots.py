import pandas as pd
from classes import ApiLoader
import plotly.graph_objects as go


def sift_out(df: pd.DataFrame, date_column: str = "year_month"):

    # Gruppen werden erstellt
    grouped = df.groupby(date_column)
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


def make_pivots(df: pd.DataFrame) -> pd.DataFrame:

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


def get_crossing_probability(df: pd.DataFrame, starting_pivot_column: int) -> dict:

    crosses = []
    probabilities = {}

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
        probabilities.update({column:probability})

    return probabilities


loader = ApiLoader()
indiz_id = 29
# Auswählen des Indizes und Grupierung nach Monaten
df = pd.read_sql(f"select * from data where indiz_id='{indiz_id}';", con=loader.init_conn())
df["date"] = pd.to_datetime(df["date"], format="%d-%m-%Y")
df = df.sort_values("date").reset_index(drop=True)
df['year_month'] = df['date'].dt.to_period('M')

# Aussortierung nach Monaten und deren Höchst-, Tiefst- und Schlusswerte
df_sifted = sift_out(df)
df_pivots = make_pivots(df_sifted)
probabilities = get_crossing_probability(df_pivots, 5)

# Erstellung eines date range im letzten Monat bis zum letzten Tag der Aufzeichnung
start_date = pd.to_datetime(df_pivots.iloc[-1,0] + "-01")
end_date = start_date + pd.offsets.MonthEnd(0)

# Erstelle einen erweiterten Dataframe
extended_dates = pd.DataFrame({"date": pd.date_range(start=start_date, end=end_date, freq='B')})

# Zusammenfassen der Daten des letzten und noch laufenden Monats
df_last_month = df[df["date"] >= start_date].loc[:, "date": "close"]
df_last_month.reset_index(drop=True, inplace=True) # Funktioniert iwie nicht

# Weiter arbeiten mit dem extended Dataframe
df_extended = pd.merge(extended_dates, df_last_month, how="left", on="date")
df_extended["pivot"] = [df_pivots.iloc[-1, 5] for x in range(len(df_extended))]
df_extended["R1"] = [df_pivots.iloc[-1, 6] for x in range(len(df_extended))]
df_extended["R2"] = [df_pivots.iloc[-1, 7] for x in range(len(df_extended))]
df_extended["R3"] = [df_pivots.iloc[-1, 8] for x in range(len(df_extended))]
df_extended["S1"] = [df_pivots.iloc[-1, 9] for x in range(len(df_extended))]
df_extended["S2"] = [df_pivots.iloc[-1, 10] for x in range(len(df_extended))]
df_extended["S3"] = [df_pivots.iloc[-1, 11] for x in range(len(df_extended))]
df_extended["P-MID-R1"] = [df_pivots.iloc[-1, 12] for x in range(len(df_extended))]
df_extended["Strike"] = df_extended["pivot"] + ((df_extended["P-MID-R1"] - df_extended["pivot"]) / 3 * 2)
df_extended["R1-MID-R2"] = [df_pivots.iloc[-1, 13] for x in range(len(df_extended))]
df_extended["R2-MID-R3"] = [df_pivots.iloc[-1, 14] for x in range(len(df_extended))]
df_extended["P-MID-S1"] = [df_pivots.iloc[-1, 15] for x in range(len(df_extended))]
df_extended["S1-MID-S2"] = [df_pivots.iloc[-1, 16] for x in range(len(df_extended))]
df_extended["S2-MID-S3"] = [df_pivots.iloc[-1, 17] for x in range(len(df_extended))]


# Nutzung des Frameworks plotly für den Candle-Stick Chart
fig = go.Figure(data=[go.Candlestick(x=df_extended["date"], open=df_extended["open"], high=df_extended["high"], low=df_extended["low"], close=df_extended["close"])])

# Hinzufügen der durchgezogenen Linien
fig.add_trace(go.Scatter(x=df_extended["date"], y=df_extended["pivot"], mode="lines", name="Pivot", line=dict(color="#000000", dash="solid")))
fig.add_trace(go.Scatter(x=df_extended["date"], y=df_extended["Strike"], mode="lines", name="Strike", line=dict(dash="solid")))
fig.add_trace(go.Scatter(x=df_extended["date"], y=df_extended["R1"], mode="lines", name=f"R1: {probabilities.get('R1')}%", line=dict(color="#00FFFF", dash="solid")))
fig.add_trace(go.Scatter(x=df_extended["date"], y=df_extended["R2"], mode="lines", name=f"R2: {probabilities.get('R2')}%", line=dict(color="#FFFF00", dash="solid")))
fig.add_trace(go.Scatter(x=df_extended["date"], y=df_extended["R3"], mode="lines", name=f"R3: {probabilities.get('R3')}%", line=dict(color="#FF0000", dash="solid")))
fig.add_trace(go.Scatter(x=df_extended["date"], y=df_extended["S1"], mode="lines", name=f"S1: {probabilities.get('S1')}%", line=dict(color="#00FFFF",dash="solid")))
fig.add_trace(go.Scatter(x=df_extended["date"], y=df_extended["S2"], mode="lines", name=f"S2: {probabilities.get('S2')}%", line=dict(color="#FFFF00", dash="solid")))
fig.add_trace(go.Scatter(x=df_extended["date"], y=df_extended["S3"], mode="lines", name=f"S3: {probabilities.get('S3')}%", line=dict(color="#FF0000", dash="solid")))
fig.add_trace(go.Scatter(x=df_extended["date"], y=df_extended["P-MID-R1"], mode="lines", name=f"P-MID-R1: {probabilities.get('P-MID-R1')}%", line=dict(color="#0000FF", dash="solid")))
fig.add_trace(go.Scatter(x=df_extended["date"], y=df_extended["R1-MID-R2"], mode="lines", name=f"R1-MID-R2: {probabilities.get('R1-MID-R2')}%", line=dict(color="#00FF00", dash="solid")))
fig.add_trace(go.Scatter(x=df_extended["date"], y=df_extended["R2-MID-R3"], mode="lines", name=f"R2-MID-R3: {probabilities.get('R2-MID-R3')}%", line=dict(color="#FFA500", dash="solid")))
fig.add_trace(go.Scatter(x=df_extended["date"], y=df_extended["P-MID-S1"], mode="lines", name=f"P-MID-S1: {probabilities.get('P-MID-S1')}%", line=dict(color="#0000FF", dash="solid")))
fig.add_trace(go.Scatter(x=df_extended["date"], y=df_extended["S1-MID-S2"], mode="lines", name=f"S1-MID-S2: {probabilities.get('S1-MID-S2')}%", line=dict(color="#00FF00", dash="solid")))
fig.add_trace(go.Scatter(x=df_extended["date"], y=df_extended["S2-MID-S3"], mode="lines", name=f"S2-MID-S3: {probabilities.get('S2-MID-S3')}%", line=dict(color="#FFA500", dash="solid")))
fig.update_layout(title="DAX Kurs", xaxis_title="Datum", yaxis_title='Preis', template='plotly')

fig.show()
# Nach dem 29.11.2024 nochmal datapi starten und erneut Daten vom Dax vom 29.11.2024 überprüfen.
# Loading CSV überarbeiten da Advanced Loader gelöscht wurde.
# pivots.py refactoren
