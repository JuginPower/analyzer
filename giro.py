import csv
import re
from pathlib import Path
from classes import SqliteDatamanager


csv_pfad = Path('data/giro')
dateien = [datei.name for datei in csv_pfad.iterdir() if "Kontoumsaetze" in datei.name]

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


def speichere_dict_als_csv(dictionary, dateipfad, zweck: str = ""):
    with open(dateipfad.replace("Kontoumsaetze_", zweck), 'w', newline='') as csvdatei:
        writer = csv.writer(csvdatei, delimiter=';')
        # Schreibe Header (Schlüssel)
        writer.writerow(dictionary.keys())
        # Schreibe Werte
        writer.writerow(dictionary.values())


if __name__ == "__main__":
    
    dm = SqliteDatamanager("/home/eugen/Schreibtisch/finance.sqlite3")

    keywords = dm.select("select kategorien.name, keywords.name from kategorien "
                         "inner join keywords on kategorien.kid=keywords.kid;")
    
    kategorien = {}

    for kat in set([k[0] for k in keywords]):
        kategorien[kat] = 0
        
    bilanz = {"Einnahmen": 0, "Ausgaben": 0, "Bilanz": 0}

    for index, name in enumerate(dateien):
        print(f"{index} eingeben für:", name)

    active = True
    custom_index = 0

    while active:
        try:
            custom_index = int(input("Eingabe: "))
        except ValueError:
            print("Falsche Eingabe")
        else:
            if custom_index < 0 or custom_index >= len(dateien):
                print("Falsche Eingabe")
            else:
                active = False

    ausgabe_datei = f'{csv_pfad}/{dateien[custom_index]}'

    with open(ausgabe_datei) as csvfile:
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
    speichere_dict_als_csv(kategorien, ausgabe_datei, "Variable_Ausgaben_")
    speichere_dict_als_csv(bilanz, ausgabe_datei, "Bilanz_")
    print(kategorien)
    print(bilanz)

    anweisung = input("Datei löschen?(j/n): ")
    if anweisung == "j":
        Path(ausgabe_datei).unlink()
