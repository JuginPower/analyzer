import csv
import re
from pathlib import Path
import sys
from datalayer import Datamanager


def to_float(str_number: str, absolut=True):

    result = None

    try:
        if len(str_number) > 7:
            result = str_number.replace(".", "_").replace(",", ".")
        
        elif len(str_number) <= 7:
            result = str_number.replace(",", ".")

        if absolut:
            result = abs(float(result))
        elif not absolut:
            result = float(result)
    
    except ValueError as err:
        return str(err)
    
    return result


def sum_kewords(keywords: dict, row: list[str]) -> str | dict:

    """Diese Funktion gibt für jedes Keyword in einem Dictionary"""

    result = {}

    for item in keywords.items():
        kategorie: str = item[0]

        result[kategorie] = 0

        for value in item[1]:
            try:
                if re.search(value, row[3] + row[4], re.IGNORECASE):
                    soll = to_float(row[-3])
                    result[kategorie] += soll

            except IndexError as err:
                return str(err)
            
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

    aditional_path = Path("/home/eugen/Dokumente").resolve()
    # sys.path.append(str(aditional_path))

    keywords = {'Lebensmittel': ["markt der prinz", "rewe", "lidl", "aldi", 
                                 "netto", "polonia", "tegut", "edeka", 
                                 "SUDE MARKET"], 
                                 'Mobilität': ["limebike", "tier mobility", 
                                               "ruhrbahn"]} # Datenbank benötigt
    
    dm = Datamanager(connection=f"{aditional_path}/finance.db")

    database_keywords = dm.select("select kategorien.name, keywords.name "
                                  "from kategorien "
                                  "inner join keywords "
                                  "on kategorien.kid=keywords.kid;")
    
    kategorien = {'Lebensmittel': 0, 'Mobilität': 0}
    bilanz = {"Einnahmen": 0, "Ausgaben": 0, "Bilanz": 0}

    with open('Kontoumsaetze_August_2024.csv') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=';')
        
        for row in spamreader:
            res = sum_kewords(keywords, row)

            if isinstance(res, dict):
                for key in res.keys():
                    kategorien[key] += res.get(key)

            bil = do_bilanzierung(row)
            
            if isinstance(bil, float):
                if bil < 0:
                    bilanz["Ausgaben"] += bil
                elif bil > 0:
                    bilanz["Einnahmen"] += bil
            
    bilanz["Bilanz"] = round(bilanz["Einnahmen"] + bilanz["Ausgaben"], 2) 
    # Eigene Dict schreiben mit round Funktion
    
    print(kategorien)
    print(bilanz)
