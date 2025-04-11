import pandas as pd
import plotly.graph_objects as go
from math import sqrt, pi, exp
from datalayer import MysqlConnectorManager
from settings import mariadb_config


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

    fig.update_layout(title=title, xaxis_title="Datum", yaxis_title='Preis', template='plotly')

    fig.show()


def choose_id(theory_name: str) -> int:
    """
    This function should simply explain the user which id stands for which index

    :theory_name: Kind of theory name for right naming purposes

    :return: the id for further evaluation
    """

    dm = MysqlConnectorManager(mariadb_config)
    indizes = [dict(indiz_id=indiz[0], indiz_name=indiz[1]) for indiz in dm.select("select * from items;")]
    indiz_ids = []
    choosed_id = None

    print(f"Please choose the indiz_id for the indiz to analyse it with the {theory_name} theory:\n")

    for indiz_row in indizes:
        indiz_id = indiz_row.get('indiz_id')
        indiz_ids.append(indiz_id)
        print(f"id {indiz_id}: {indiz_row.get('indiz_name')}")

    print()
    while True:
        try:
            choosed_id = int(input("id: "))
        except ValueError:
            print(choosed_id, "is not an integer!")
        else:
            if choosed_id in indiz_ids:
                break
            else:
                print(f"There is no {choosed_id} in the database, please try another!")
                continue

    return choosed_id


def choose_theory():

    theories = {1: "pivots", 2: "normal distribution", 3: "kneighbors regressions"}
    print()
    while True:

        for item in theories.items():
            print("Press " + str(item[0]) + " for:", item[1])


        theory_number = input("Choose the theory or q to quit: ")
        if theory_number in ("q", "Q"):
            break

        try:
            theory_number = int(theory_number)
        except ValueError:
            print("Only numbers allowed!")
            continue
        else:
            match theory_number:
                case 1: pivots_process()
                case 2: normal_distribution_process()
                case 3: ai_process()
                case _: continue

