import pandas as pd
import plotly.graph_objects as go
from math import sqrt, pi, exp
from pathlib import Path
import matplotlib.cm as cm
import matplotlib.colors as mcolors


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


def get_density(x: pd.Series | list, orig_density: dict):
    """A function for calculating the density of a given x value.

    :param x: The x value for which the density is calculated.

    :param orig_density: The original density of the x value.

    return: The density of the x value as a floating point number.

    """
    result = 0
    for val in x:
        result += orig_density.get(val)
    return result


def sort_dict_values(item: dict) -> int | float:
    """
    A custom sort helper function to identify with builtin which property needs to be sorted.

    :param item: The dictionary to sort
    :return: An integer or float
    """
    return list(item.values())[0]


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

    fig.update_layout(title=title, xaxis_title="Date", yaxis_title='Price', template='plotly')

    fig.show()


def get_color(value, norm):
    """
    Ermittelt die Farbe basierend auf dem normalisierten Wert
    """
    cmap = cm.get_cmap('jet')  # Jet-Colormap für Rot-Blau Übergang
    rgba = cmap(norm(value))
    hex_color = mcolors.to_hex(rgba)
    return hex_color


def get_csv_file(csv_pfad = Path('data/stocks')) -> str:

    """A function to get a specific csv file in a given directory.

    :csv_pfad: The directory to search for csv files.

    :return: The path to the selected csv file."""

    files = [file.name for file in csv_pfad.iterdir()]

    for index, name in enumerate(files):
        print(f"{index} eingeben für:", name)

    active = True
    custom_index = 0

    while active:
        try:
            custom_index = int(input("Eingabe: "))
        except ValueError:
            print("Falsche Eingabe")
        else:
            if custom_index < 0 or custom_index >= len(files):
                print("Falsche Eingabe")
            else:
                active = False

    output_file = f'{csv_pfad}/{files[custom_index]}'

    return output_file


if __name__ == "__main__":

    pass
