import pandas as pd
from classes import ApiLoader
import plotly.graph_objects as go


loader = ApiLoader()
indiz_id = 26
title = loader.select(f"select name from indiz where indiz_id='{indiz_id}';")[0][0]

def sift_out(df: pd.DataFrame, date_column: str = "year_month"):

    """Errechnet für jeden Monat die Höchs-, Tiefst- und Schlusskurse"""

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


def get_crossing_probability(df: pd.DataFrame, starting_pivot_column: int) -> dict:

    """Errechnet die Wahrscheinlichkeit der Kreuzung der Pivot-Linien anhand historischer Daten"""

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


def merge_pivots(extended_dates_dataframe: pd.DataFrame, last_month_dataframe: pd.DataFrame, pivots_dataframe: pd.DataFrame, starting_column=5):

    """Nimmt ein Dataframe vom aktuellen vollständigen Monat und merged diesen mit den letzten pivots für diesen Monat."""
     
    df_merged = pd.merge(extended_dates_dataframe, last_month_dataframe, how="left", on="date").copy(deep=True)
    pivot_columns = [c for c in pivots_dataframe.columns]

    for column in pivot_columns[starting_column:]:

        df_merged[column] = [pivots_dataframe.iloc[-1, pivot_columns.index(column)] for x in range(len(df_merged))]

    df_merged["Strike"] = df_merged["pivot"] + ((df_merged["P-MID-R1"] - df_merged["pivot"]) / 3 * 2)

    return df_merged


# Auswählen des Indizes und Grupierung nach Monaten
df = pd.read_sql(f"select * from data where indiz_id='{indiz_id}';", con=loader.init_conn())
df["date"] = pd.to_datetime(df["date"], format="%d-%m-%Y") # Ich habe verschiedene Datumsformate in der Datenbank
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

# Hier kommt das Merging des aktuellen vollständigen Monats mit den letzten Pivotlinien
df_merged = merge_pivots(extended_dates, df_last_month, df_pivots)

# Nutzung des Frameworks plotly für den Candle-Stick Chart
fig = go.Figure(data=[go.Candlestick(x=df_merged["date"], open=df_merged["open"], high=df_merged["high"], low=df_merged["low"], close=df_merged["close"])])

# Hinzufügen der durchgezogenen Linien
fig.add_trace(go.Scatter(x=df_merged["date"], y=df_merged["pivot"], mode="lines", name="Pivot", line=dict(color="#000000", dash="solid")))
fig.add_trace(go.Scatter(x=df_merged["date"], y=df_merged["Strike"], mode="lines", name="Strike", line=dict(dash="solid")))
fig.add_trace(go.Scatter(x=df_merged["date"], y=df_merged["R1"], mode="lines", name=f"R1: {probabilities.get('R1')}%", line=dict(color="#00FFFF", dash="solid")))
fig.add_trace(go.Scatter(x=df_merged["date"], y=df_merged["R2"], mode="lines", name=f"R2: {probabilities.get('R2')}%", line=dict(color="#FFFF00", dash="solid")))
fig.add_trace(go.Scatter(x=df_merged["date"], y=df_merged["R3"], mode="lines", name=f"R3: {probabilities.get('R3')}%", line=dict(color="#FF0000", dash="solid")))
fig.add_trace(go.Scatter(x=df_merged["date"], y=df_merged["S1"], mode="lines", name=f"S1: {probabilities.get('S1')}%", line=dict(color="#00FFFF",dash="solid")))
fig.add_trace(go.Scatter(x=df_merged["date"], y=df_merged["S2"], mode="lines", name=f"S2: {probabilities.get('S2')}%", line=dict(color="#FFFF00", dash="solid")))
fig.add_trace(go.Scatter(x=df_merged["date"], y=df_merged["S3"], mode="lines", name=f"S3: {probabilities.get('S3')}%", line=dict(color="#FF0000", dash="solid")))
fig.add_trace(go.Scatter(x=df_merged["date"], y=df_merged["P-MID-R1"], mode="lines", name=f"P-MID-R1: {probabilities.get('P-MID-R1')}%", line=dict(color="#0000FF", dash="solid")))
fig.add_trace(go.Scatter(x=df_merged["date"], y=df_merged["R1-MID-R2"], mode="lines", name=f"R1-MID-R2: {probabilities.get('R1-MID-R2')}%", line=dict(color="#00FF00", dash="solid")))
fig.add_trace(go.Scatter(x=df_merged["date"], y=df_merged["R2-MID-R3"], mode="lines", name=f"R2-MID-R3: {probabilities.get('R2-MID-R3')}%", line=dict(color="#FFA500", dash="solid")))
fig.add_trace(go.Scatter(x=df_merged["date"], y=df_merged["P-MID-S1"], mode="lines", name=f"P-MID-S1: {probabilities.get('P-MID-S1')}%", line=dict(color="#0000FF", dash="solid")))
fig.add_trace(go.Scatter(x=df_merged["date"], y=df_merged["S1-MID-S2"], mode="lines", name=f"S1-MID-S2: {probabilities.get('S1-MID-S2')}%", line=dict(color="#00FF00", dash="solid")))
fig.add_trace(go.Scatter(x=df_merged["date"], y=df_merged["S2-MID-S3"], mode="lines", name=f"S2-MID-S3: {probabilities.get('S2-MID-S3')}%", line=dict(color="#FFA500", dash="solid")))
fig.update_layout(title=title, xaxis_title="Datum", yaxis_title='Preis', template='plotly')

fig.show()
# Nach dem 29.11.2024 nochmal datapi starten und erneut Daten vom Dax vom 29.11.2024 überprüfen.
# Loading CSV überarbeiten da Advanced Loader gelöscht wurde.
# Auswahl von Indizien hinzufügen. Dabei um die verschiedenen Datumsformate in der Datenbank kümmern
# Optional, fig überarbeiten.