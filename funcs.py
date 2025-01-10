import pandas as pd
import plotly.graph_objects as go
from math import sqrt, pi, exp
from copy import copy


def to_float(str_number: str, absolut=False) -> float:

    """
    Formatiert einen String in eine Fließkommazahl.

    :param str_number: Der String der formatiert wird.
    :param absolut: Bestimmt, ob die Fließkommazahl einen absoluten Wert darstellen soll oder nicht.
    :return: Gibt die fertig transformierte Fließkommazahl zurück.
    """

    result = None

    try:
        if len(str_number) >= 7:
            result = str_number.replace(".", "_").replace(",", ".")

        elif len(str_number) < 7:
            result = str_number.replace(",", ".")

        if absolut:
            result = abs(float(result))
        elif not absolut:
            result = float(result)

    except ValueError as err:
        raise err

    except TypeError as err:
        raise err

    return result


def get_std(sample: list, population=False) -> float:

    """
    Gibt die Standardabweichung zurück.

    :param sample: Die Population oder Probe.
    :param population: Entscheided, ob es sich um eine vollständige Größe der Population handelt oder nur eine Probe.
    :return: Gibt die Standardabweichung bzw. Fließkommazahl zurück.
    """

    divide = 0

    if not population:
        divide += 1

    mean = sum(sample) / len(sample)
    return sqrt(sum([(s - mean)**2 for s in sample]) / (len(sample) - divide))


def get_gaus_normald(x, mu, sigma) -> dict:

    """
    Berechnet den Wert der Normalverteilungsfunktion für einen gegebenen x-Wert.

    :param x: Der Punkt, an dem die Dichte berechnet wird.
    :param mu: Der Mittelwert der Verteilung.
    :param sigma: Die Standardabweichung.
    :return: Gibt die Dichte an Punkt x der Normalverteilungsfunktion als dictionary zurück.
    """

    numerator = 1
    denominator = sqrt(2 * pi * sigma**2)
    exponent = -((x - mu)**2) / (2 * sigma**2)

    return {"x": x, "dense": (numerator / denominator) * exp(exponent)}


def get_iqrs(sample: list) -> dict:

    """
    Berechnet die Interquartilsabstände aus einer Probe.

    :param sample: Die Probe oder Population.
    :return: Gibt ein dictionary mit den Interquartilsabständen q1, q2, q3, q4
    """

    sample.sort()

    n = len(sample)
    q1 = n // 4
    q2 = n // 2
    q3 = 3 * n // 4

    return {"quartile1": sample[:q1], "quartile2": sample[q1:q2], "quartile3": sample[q2:q3], "quartile4": sample[q3:]}


def remove_outliers(sample: list, quartiles: dict, factor=1.5):

    """
    Berechnet die Untergrenze (unterer Whisker) und Obergrenze (oberer Whisker) einer Population oder Probe und entfernt
    die Außreißer.

    :param sample: Die Liste der Daten die bereinigt werden soll.
    :param quartiles: Die Perzentile in einem Dictionary für die Berechnung der Ẃhisker.
    :param factor: Der Faktor der die Größe der Grenzen bzw. Ausreißer bestimmt.
    :return: Gibt ein von Außreißern bereinigte Liste der Population zurück
    """

    q1 = quartiles.get("quartile2")[0]
    q3 = quartiles.get("quartile4")[0]
    iqr = q3 - q1
    whisker_low = q1 - factor * iqr
    whisker_high = q3 + factor * iqr

    return [s for s in sample if whisker_high >= s >= whisker_low]


def show_graph_objects(dataframe: pd.DataFrame, title: str, *args):

    """

    :param dataframe: Das zu zeichnende Pandas Dataframe.
    :param title: Der Titel des Plots.
    :param start_column: Die Spalte ab der zusätzlichen Linie gezeichnet werden sollen.
    :param args: Zusätzliche Argumente wie die Wahrscheinlichkeitsanzeigen.
    :return: Gibt nichts zurück. Erstellt eine Webapp, die einen interaktiven Chart zeigt.
    """

    pivot_columns = [c for c in dataframe.columns]

    fig = go.Figure(data=[go.Candlestick(x=dataframe["date"], open=dataframe["open"], high=dataframe["high"], low=dataframe["low"],
                                         close=dataframe["close"])])

    for column in pivot_columns[pivot_columns.index('close') + 1:]:

        if len(args) > 0:
            if isinstance(args[0], dict): # Verbessern vllt. mit dict key Identifikation
                fig.add_trace(go.Scatter(x=dataframe["date"], y=dataframe[column], mode="lines",
                                         name=column + f": {args[0].get(column)}", line=dict(dash="solid")))
        else:
            fig.add_trace(
                go.Scatter(x=dataframe["date"], y=dataframe[column], mode="lines", name=column, line=dict(dash="solid")))

    fig.update_layout(title=title, xaxis_title="Datum", yaxis_title='Preis', template='plotly')

    fig.show()


def crossing_propability(df: pd.DataFrame): # noch nicht fertig

    crosses = []
    probabilities = {}
    len_counter = 0

    for index, row in df.iterrows():

        high_spreads = []
        low_spreads = []
        index = int(index)

        while index >= 0:

            row = df.loc[index]
            high_spreads.append(row["high"] - row["open"])
            low_spreads.append(row["open"] - row["low"])

            index -= 1

        iqrs_high_spreads = get_iqrs(high_spreads)
        iqrs_low_spreads = get_iqrs(low_spreads)

        high_spreads_cleaned = remove_outliers(copy(high_spreads), iqrs_high_spreads)
        low_spreads_cleaned = remove_outliers(copy(low_spreads), iqrs_low_spreads)
        mean_high_cleaned = sum(high_spreads_cleaned) / len(high_spreads_cleaned)
        mean_low_cleaned = sum(low_spreads_cleaned) / len(low_spreads_cleaned)

        high_std = get_std(high_spreads_cleaned)
        low_std = get_std(low_spreads_cleaned)

        normalds_high = [get_gaus_normald(x, mean_high_cleaned, high_std) for x in high_spreads_cleaned]
        normalds_low = [get_gaus_normald(x, mean_low_cleaned, low_std) for x in low_spreads_cleaned]

        permissible_deviation_high = round(mean_high_cleaned + high_std, 3)
        permissible_deviation_low = round(mean_low_cleaned + low_std, 3)