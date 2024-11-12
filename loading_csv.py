from funcs import to_float, get_database_file
import pandas as pd
import sqlite3


database_file = get_database_file()
data_file = "data/DAX-Weekly-09.01.2014-03.11.2024.csv"
conn = sqlite3.connect(database_file)
df = pd.read_csv(data_file)

for column in df.columns:
    try:
        df[column] = df[column].apply(to_float)
    except ValueError:
        continue

    except TypeError as err:
        print("Error raised in column:", column)

df.to_sql(name="data", con=conn, if_exists='append', index_label=['date', 'indiz_id', 'price'])
# Muss noch herausfinden wie ich nur bestimmte Spalten in die Datenbank schreibe.
# Brauche eine in memory Testdatenbank
# Muss die Datenbank auch redesignen, ich brauche low, high, close Spalten.
# Muss denke ich auch die Häufigkeit des Crawlers höher machen.
# Brauche eine Tabelle die temporär in fünf bis 15-Minuten-Takt Daten nur für einen ganzen Tag speichert.