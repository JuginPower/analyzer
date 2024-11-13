from funcs import to_float
import pandas as pd


# data_file = "data/DAX-Daily-07.01.2014-01.11.2024.csv"
# data_file = "data/DAX-Weekly-09.01.2014-03.11.2024.csv"
data_file = "data/DAX-Monthly-03.01.2000-12.11.2024.csv"
df = pd.read_csv(data_file)

crosses = []

for column in df.columns:
    if column == "Datum":
        continue
    else:
        try:
            df[column] = df[column].apply(to_float)
        except ValueError:
            continue

        except TypeError as err:
            print("Error raised in column:", column)

# Entfernen von Volumen und Prozenten.
df.drop(columns=df.columns[-2:], inplace=True)

# Umkehrung der Reihenfolge der Zeilen da anti chronologisch.
df = df.iloc[::-1].reset_index(drop=True)

df["pivot"] = round((df["Hoch"].shift(1) + df["Tief"].shift(1) + df["Zuletzt"].shift(1)) / 3, 2)
df["R1"] = round(2 * df["pivot"] - df["Tief"].shift(1), 2)
df["R2"] = round(df["pivot"] + (df["Hoch"].shift(1) - df["Tief"].shift(1)), 2)
df["R3"] = round(df["R1"] + (df["Hoch"].shift(1) - df["Tief"].shift(1)), 2)

df["S1"] = round(2 * df["pivot"] - df["Hoch"].shift(1), 2)
df["S2"] = round(df["pivot"] - (df["Hoch"].shift(1) - df["Tief"].shift(1)), 2)
df["S3"] = round(df["S1"] - (df["Hoch"].shift(1) - df["Tief"].shift(1)), 2)

df["P-MID-R1"] = round(df["pivot"] + ((df["R1"] - df["pivot"]) / 2), 2)
df["R1-MID-R2"] = round(df["R1"] + ((df["R2"] - df["R1"]) /2), 2)
df["R2-MID-R3"] = round(df["R2"] + ((df["R3"] - df["R2"]) /2), 2)

df["P-MID-S1"] = round(df["pivot"] - ((df["pivot"] - df["S1"]) / 2), 2)
df["S1-MID-S2"] = round(df["S1"] - ((df["S1"] - df["S2"]) / 2), 2)
df["S2-MID-S3"] = round(df["S2"] - ((df["S2"] - df["S3"]) / 2), 2)

for index, row in df.iterrows():
    try:
        previous_row = df.loc[int(index) - 1]
    except KeyError:
        continue
    else:
        for column in df.columns[5:]:

            if column[0] == "R" or column == "P-MID-R1":
                if row["Hoch"] > previous_row[column]:
                    crosses.append({"pivotname": column, "row": row})

            elif column[0] == "S" or column == "P-MID-S1":
                if row["Tief"] < previous_row[column]:
                    crosses.append({"pivotname": column, "row": row})

for column in df.columns[5:]:
    probability = round(([d.get("pivotname") for d in crosses].count(column) / len(df)) * 100, 3)
    print(f"The probability that the price reaches the {column} line: {probability} %")


# Bei R1mid 74,16 %