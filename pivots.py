from funcs import to_float
import pandas as pd


data_file = "data/DAX-Monthly-03.01.2000-12.11.2024.csv"
df = pd.read_csv(data_file)

crosses = []
pivot_name = "R1mid"

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
df["R1mid"] = round(df["pivot"] + ((df["R1"] - df["pivot"]) / 2), 2)
df["R2"] = round(df["pivot"] + (df["Hoch"].shift(1) - df["Tief"].shift(1)), 2)
df["R3"] = round(df["R1"] + (df["Hoch"].shift(1) - df["Tief"].shift(1)), 2)

df["S1"] = round(2 * df["pivot"] - df["Hoch"].shift(1), 2)
df["S2"] = round(df["pivot"] - (df["Hoch"].shift(1) - df["Tief"].shift(1)), 2)
df["S3"] = round(df["S1"] - (df["Hoch"].shift(1) - df["Tief"].shift(1)), 2)

for index, row in df.iterrows():
    try:
        previous_row = df.loc[int(index) - 1]
    except KeyError:
        continue
    else:
        if row["Hoch"] > previous_row[pivot_name]:
            crosses.append(row)

print(f"Chance to cross {pivot_name}:", len(crosses) / len(df))

# Bei R1mid 74,16 %