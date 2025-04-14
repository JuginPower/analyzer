from funcs import choose_id, get_iqrs, remove_outliers, get_gaus_normald, get_std, show_graph_objects
from copy import copy
from classes import MainAnalyzer, PivotMaker
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.linear_model import LinearRegression
import pandas as pd


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


def normal_distribution_process():

    """
    Starts the theory process of normal distribution

    """

    choosed_id = choose_id("normal distributions")
    ma = MainAnalyzer(choosed_id)

    df_orig = ma.prepare_dataframe('M', 'sift_out')
    high_spreads = [h - o for h, o in zip(df_orig["high"], df_orig["open"])]  # May Scatterplott
    low_spreads = [o - l for o, l in zip(df_orig["open"], df_orig["low"])]

    iqrs_high_spreads = get_iqrs(high_spreads)
    iqrs_low_spreads = get_iqrs(low_spreads)

    high_spreads_cleaned = remove_outliers(copy(high_spreads), iqrs_high_spreads)  # May Scatterplott
    low_spreads_cleaned = remove_outliers(copy(low_spreads), iqrs_low_spreads)
    mean_high_cleaned = sum(high_spreads_cleaned) / len(high_spreads_cleaned)
    mean_low_cleaned = sum(low_spreads_cleaned) / len(low_spreads_cleaned)

    high_std = get_std(high_spreads_cleaned)
    low_std = get_std(low_spreads_cleaned)

    normalds_high = [get_gaus_normald(x, mean_high_cleaned, high_std) for x in high_spreads_cleaned]
    normalds_low = [get_gaus_normald(x, mean_low_cleaned, low_std) for x in low_spreads_cleaned]
    normalds_high.sort(key=lambda k: k["dense"])
    normalds_low.sort(key=lambda k: k["dense"])
    max_dense_high = normalds_high[-1]["x"]
    max_dense_low = normalds_low[-1]["x"]

    max_deviation_high = round(max_dense_high + high_std, 3)
    max_deviation_low = round(max_dense_low + low_std, 3)

    df_last_month = ma.get_last_month(df_orig)
    df_last_month["mean_high"] = round(df_orig.iloc[-1, 3] + max_dense_high, 3)
    df_last_month["mean_low"] = round(df_orig.iloc[-1, 3] - max_dense_low, 3)
    df_last_month["max_high"] = round(df_orig.iloc[-1, 3] + max_deviation_high, 3)
    df_last_month["max_low"] = round(df_orig.iloc[-1, 3] - max_deviation_low, 3)

    show_graph_objects(df_last_month, ma.title)


def ai_process():
    # Data preparation
    item_id = choose_id("KNeighbors & Linear Regression")
    ma = MainAnalyzer(item_id)
    df_normal = ma.prepare_dataframe('W', 'sift_out')

    # Keep one last row secret for the pending month
    df_final_test = df_normal.tail(1).copy()
    df_normal.drop([len(df_normal) - 1], inplace=True)

    # Data preparation for sklearn
    X = df_normal.loc[:, ["open"]].to_numpy()
    y = df_normal.loc[:, ["close"]].to_numpy()

    # Some extra unknown data
    X_final = df_final_test.loc[:, ["open"]].to_numpy()
    y_final = df_final_test.loc[:, ["close"]].to_numpy()

    # Splitting the data for training and tests
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25)

    ### LinearRegression GridSearch ###
    lr = LinearRegression()
    param_grid_lr = {
        "fit_intercept": [True, False],
        "positive": [True, False]
    }

    grid_search_lr = GridSearchCV(lr, param_grid_lr, cv=5, refit=True, scoring='neg_mean_absolute_percentage_error', verbose=1)
    grid_search_lr.fit(X_train, y_train)

    print("\n[LinearRegression] Best training score:", grid_search_lr.best_score_)
    print("[LinearRegression] Best training params:", grid_search_lr.best_params_)

    # Test prediction (Linear Regression)
    test_accuracy_lr = grid_search_lr.score(X_test, y_test)
    print("\n[LinearRegression] Test Accuracy:", test_accuracy_lr)

    # Live Training mit allen Daten (Linear Regression)
    grid_search_lr.fit(X, y)
    print("\n[LinearRegression] Best live score:", grid_search_lr.best_score_)
    print("[LinearRegression] Best live params:", grid_search_lr.best_params_)

    # LinearRegression Final Prediction
    final_prediction_lr = grid_search_lr.predict(X_final)
    print(f"\n[LinearRegression] Final Prediction for {df_final_test.iloc[0, 0]}: {final_prediction_lr[0][0]}")
    print(f"Bruce Danel says 'Das ist die Wahrheit:' {y_final[0][0]}")
    print(f"Opening at {df_final_test.iloc[0, -2]}")


def pivots_process():

    """
    Starts the theory process of pivots.
    """
    choosed_id = choose_id("pivots")
    pm = PivotMaker(choosed_id)
    df_pivots: pd.DataFrame = pm.prepare_dataframe('M', 'sift_out', 'make_pivots')
    df_last_month: pd.DataFrame = pm.get_last_month(df_pivots)
    propabilities: dict = pm.get_crossing_probability(df_pivots, 2000)
    show_graph_objects(df_last_month, pm.title, propabilities)


if __name__=='__main__':
    theory_name = choose_theory()
    print("Programm stops now!")
