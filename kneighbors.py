from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.neighbors import KNeighborsRegressor
from classes import MainAnalyzer
from funcs import choose_id
from pathlib import Path
import os



BASE_DIR = Path(__file__).resolve().parent.parent
path_database = os.path.join(BASE_DIR, "finance.sqlite3")

# Data preparation
indiz_id = choose_id(path_database, "KNeighbors Regression")
ma = MainAnalyzer(indiz_id)
df_monthly = ma.prepare_dataframe('year_month', 'sift_out')

# Do not need the last month
df_monthly.drop([len(df_monthly)-1], inplace=True)

# Keep one last row secret
df_final_test = df_monthly.tail(1).copy()
df_monthly.drop([len(df_monthly)-1], inplace=True)

# Data preparation for sklearn
X = df_monthly.loc[:, ["open", "high", "low"]]
y = df_monthly.loc[:, ["close"]]
X = X.to_numpy()
y = y.to_numpy()

# Some extra unknown data
X_final = df_final_test.loc[:, ["open", "high", "low"]]
y_final = df_final_test.loc[:, ["close"]]
X_final = X_final.to_numpy()
y_final = y_final.to_numpy()

# Splitting the data for main training and tests
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25)

knn = KNeighborsRegressor()
param_grid = {"n_neighbors": range(1, 21, 1),
              "weights": ["uniform", "distance"],
              "p": [1, 2],
              "algorithm": ['auto']}

grid_search = GridSearchCV(knn, param_grid, cv=5, refit=True, scoring='r2', verbose=1)

# training the grid search
grid_search.fit(X_train, y_train)
train_best_score = grid_search.best_score_
train_best_params = grid_search.best_params_
print("Best training score:", train_best_score)
print("Best training params:", train_best_params)

# Test prediction
test_accuracy = grid_search.score(X_test, y_test)
print("Test Accuracy:", test_accuracy)

# prediction
final_prediction = grid_search.predict(X_final)
print(f"The final prediction for {df_final_test['year_month']}:\n{final_prediction}")
print(f"Bruce Danel says 'Das ist die Wahrheit:' {y_final}")
