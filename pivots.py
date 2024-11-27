import pandas as pd
from classes import AdvancedLoader
import plotly.graph_objects as go


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
indiz_id = 29
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

# Erstelle einen erweiterten Dataframe
extended_dates = pd.DataFrame({"date": pd.date_range(start=start_date, end=end_date, freq='B')})

# Zusammenfassen der Daten des letzten und noch laufenden Monats
df_last_month = df[df["date"] >= start_date].loc[:, "date": "close"]
df_last_month.reset_index(drop=True, inplace=True) # Funktioniert iwie nicht

# Weiter arbeiten mit dem extended Dataframe
df_extended = pd.merge(extended_dates, df_last_month, how="left", on="date")
df_extended["pivot"] = [df_pivots.iloc[-1, 5] for x in range(len(df_extended))]
df_extended["P-MID-R1"] = [df_pivots.iloc[-1, 12] for x in range(len(df_extended))]
df_extended["R1"] = [df_pivots.iloc[-1, 6] for x in range(len(df_extended))]
df_extended["Strike"] = df_extended["pivot"] + ((df_extended["P-MID-R1"] - df_extended["pivot"]) / 3 * 2)

# Nutzung des Frameworks plotly für den Candle-Stick Chart
fig = go.Figure(data=[go.Candlestick(x=df_extended["date"], open=df_extended["open"], high=df_extended["high"], low=df_extended["low"], close=df_extended["close"])])

# Hinzufügen der durchgezogenen Linien
fig.add_trace(go.Scatter(x=df_extended["date"], y=df_extended["pivot"], mode="lines", name="Pivot", line=dict(color="#000000", dash="solid")))
fig.add_trace(go.Scatter(x=df_extended["date"], y=df_extended["Strike"], mode="lines", name="Strike", line=dict(color="#e19e13", dash="solid")))
fig.add_trace(go.Scatter(x=df_extended["date"], y=df_extended["P-MID-R1"], mode="lines", name="P-MID-R1", line=dict(color="#338fff", dash="solid")))
fig.add_trace(go.Scatter(x=df_extended["date"], y=df_extended["R1"], mode="lines", name="R1", line=dict(color="#41e926", dash="solid")))
fig.update_layout(title="DAX Kurs", xaxis_title="Datum", yaxis_title='Preis', template='plotly')

fig.show()
# Am 27.11.2024 um 23:50 Uhr delete Anfrage an datapi schicken
# Historische Daten für den 27.11.2024 für den Dax uploaden.
# Titel und Wharscheinlichkeit der Kreuzungen hinzufügen.
# Alle pivot Linien hinzufügen.
# Am 29.11.2024 im Laufe des Tages loading_datapi starten.
# Die Richtigkeit der erfassten Kurse mit den Daten für DAX aus TWS vergleichen.
# Am 03.12.2024 im Laufe des Tages loading_datapi starten.
# Die Richtigkeit der erfassten Kurse mit den Daten für DAX aus TWS vergleichen.
# In GitHub (privat) einpflegen und Master Branch auf Laptop herunterladen.
