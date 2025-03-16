import csv
import re
from pathlib import Path
import os
from datalayer import SqliteDatamanager


BASE_DIR = Path(__file__).resolve().parent.parent

def to_float(str_number: str, absolut=True):

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
        return str(err)
    
    return result


def sum_kewords(keywords: list, row: list[str]) -> str | dict:

    """Diese Funktion addiert den Sollwert einer jeden Kategorie bei einem 
    Match der Row mit den Keywords"""

    result = {}

    for val in keywords:
        kategorie: str = val[0]

        result[kategorie] = 0
    
    for val in keywords:
        try:
            if re.search(val[1], row[3] + row[4], re.IGNORECASE):
                soll = to_float(row[-3])
                result[val[0]] += soll

        except (IndexError, TypeError):
            continue
    
    if sum(result.values()) == 0 and len(row) == 18:
        return f"Nicht erfasst: {row[0] + ", " + row[2] + " " + row[3] + " " + row[4] + ": " + row[-3] + row[-2]}"

    return result


def do_bilanzierung(row: list):

    try:
        if len(row) == 18:
            if len(row[-2]) > 0:
                return to_float(row[-2], False)
            return to_float(row[-3], False)
        
    except IndexError as err:
        return str(err)


if __name__ == "__main__":
    
    dm = SqliteDatamanager(os.path.join(BASE_DIR, "finance.sqlite3"))

    keywords = dm.select("select kategorien.name, keywords.name from kategorien "
                         "inner join keywords on kategorien.kid=keywords.kid;")
    
    kategorien = {}

    for kat in set([k[0] for k in keywords]):
        kategorien[kat] = 0
        
    bilanz = {"Einnahmen": 0, "Ausgaben": 0, "Bilanz": 0}

    with open('data/giro/Kontoumsaetze_Februar_2025.csv') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=';')
        
        for row in spamreader:
            res = sum_kewords(keywords, row)

            if isinstance(res, dict):
                for key in res.keys():
                    kategorien[key] += res.get(key)
            
            elif isinstance(res, str):
                print(res)

            bil = do_bilanzierung(row)
            
            if isinstance(bil, float):
                if bil < 0:
                    bilanz["Ausgaben"] += bil
                elif bil > 0:
                    bilanz["Einnahmen"] += bil
            
    bilanz["Bilanz"] = round(bilanz["Einnahmen"] + bilanz["Ausgaben"], 2) 
    # Eigene Dict schreiben mit round Funktion
    
    print()
    print(kategorien)
    print(bilanz)
