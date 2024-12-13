import pandas as pd
from classes import BaseLoader
import plotly.graph_objects as go


def prepare_dataframe(indiz_id: int, *args) -> pd.DataFrame:

    loader = BaseLoader()
    df = pd.read_sql(f"select * from data where indiz_id='{indiz_id}';", con=loader.init_conn())
    df["date"] = pd.to_datetime(df["date"], format="%d-%m-%Y")
    df = df.sort_values("date").reset_index(drop=True)

    for arg in args:

        if arg == "year_month":
            # Wenn die Spalte year_month gebraucht wird
            df['year_month'] = df['date'].dt.to_period('M')

        if arg == "sift_out":
            # Wenn andere Datensätze aussortiert werden müssen
            df = sift_out(df)

    return df


def sift_out(df: pd.DataFrame, date_column: str = "year_month") -> pd.DataFrame:

    """Errechnet für jeden Monat die Höchs-, Tiefst- und Schlusskurse und gibt nur diese in einem neuen dataframe zurück"""

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


def show_graph_objects(df: pd.DataFrame, title: str, *args, kind='candle'):

    fig = None
    df.drop(columns='indiz_id', inplace=True)
    pivot_columns = [c for c in df.columns]

    if kind == 'candle':
        probabilities: dict = args[0]
        fig = go.Figure(data=[go.Candlestick(x=df["date"], open=df["open"], high=df["high"], low=df["low"],
                                             close=df["close"])])

        for column in pivot_columns[5:]:

            if probabilities.get(column):
                fig.add_trace(go.Scatter(x=df["date"], y=df[column], mode="lines",
                                         name=column + f": {probabilities.get(column)}", line=dict(dash="solid")))
            else:
                fig.add_trace(go.Scatter(x=df["date"], y=df[column], mode="lines", name=column, line=dict(dash="solid")))


    fig.update_layout(title=title, xaxis_title="Datum", yaxis_title='Preis', template='plotly')

    fig.show()