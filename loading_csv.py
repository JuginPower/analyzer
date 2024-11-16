from funcs import to_float
import pandas as pd


data_file = "data/DAX-Monthly-03.01.2000-12.11.2024.csv"
df = pd.read_csv(data_file)

for column in df.columns:
    try:
        df[column] = df[column].apply(to_float)
    except ValueError:
        continue

    except TypeError as err:
        print("Error raised in column:", column)


# Muss noch herausfinden wie ich nur bestimmte Spalten in die Datenbank schreibe.
# Brauche eine in memory Testdatenbank
# Muss die Datenbank auch redesignen, ich brauche low, high, close Spalten.
# Muss denke ich auch die Häufigkeit des Crawlers höher machen.
# Brauche eine Tabelle die temporär in fünf bis 15-Minuten-Takt Daten nur für einen ganzen Tag speichert.