import pandas as pd
import plotly.graph_objects as go
from math import sqrt, pi, exp


def to_float(str_number: str, absolut=False) -> float:

    """
    Formats a string into a floating point number.

    :param str_number: The string to be formatted.
    :param absolut: Determines whether the floating point number should represent an absolute value or not.
    :return: Returns the completely transformed floating point number.
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
    Returns the standard deviation.

    :param sample: The population or sample.
    :param population: Decides whether this is a full size of the population or just a sample.
    :return: Returns the standard deviation or floating point number.
    """

    divide = 0

    if not population:
        divide += 1

    mean = sum(sample) / len(sample)
    return sqrt(sum([(s - mean)**2 for s in sample]) / (len(sample) - divide))


def get_gaus_normald(x, mu, sigma) -> dict:

    """
    Calculates the value of the normal distribution function for a given x value.

    :param x: The point at which the density is calculated.
    :param mu: The mean of the distribution.
    :param sigma: The standard deviation.
    :return: Returns the density at point x of the normal distribution function as a dictionary.
    """

    numerator = 1
    denominator = sqrt(2 * pi * sigma**2)
    exponent = -((x - mu)**2) / (2 * sigma**2)

    return {"x": x, "dense": (numerator / denominator) * exp(exponent)}


def get_iqrs(sample: list) -> dict:

    """
    Calculates the interquartile ranges from a sample.

    :param sample: The sample or population.
    :return: Returns a dictionary with the interquartile ranges q1, q2, q3, q4
    """

    sample.sort()

    n = len(sample)
    q1 = n // 4
    q2 = n // 2
    q3 = 3 * n // 4

    return {"quartile1": sample[:q1], "quartile2": sample[q1:q2], "quartile3": sample[q2:q3], "quartile4": sample[q3:]}


def remove_outliers(sample: list, quartiles: dict, factor=1.5):

    """
    Calculates the lower limit (lower whisker) and upper limit (upper whisker) of a population or sample and removes
    the outliers.

    :param sample: The list of data to be cleaned.
    :param quartiles: The percentiles in a dictionary for calculating the quartiles.

    :param factor: The factor that determines the size of the limits or outliers.

    :return: Returns a list of the population cleaned of outliers
    """

    q1 = quartiles.get("quartile2")[0]
    q3 = quartiles.get("quartile4")[0]
    iqr = q3 - q1
    whisker_low = q1 - factor * iqr
    whisker_high = q3 + factor * iqr

    return [s for s in sample if whisker_high >= s >= whisker_low]


def show_graph_objects(dataframe: pd.DataFrame, title: str, *args):

    """
    This function uses plotly to start an interactive chart in the browser.

    :param dataframe: The Pandas dataframe to plot.
    :param title: The title of the plot.
    :param start_column: The column to start plotting the additional line.
    :param args: Additional arguments such as the probability indicators.
    :return: Returns nothing. Creates a webapp that shows an interactive chart.
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

"""
-- Not finished yet
def crossing_propability(df: pd.DataFrame):

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
        permissible_deviation_low = round(mean_low_cleaned + low_std, 3)"""