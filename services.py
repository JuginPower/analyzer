import csv
import re


def to_float(str_number: str, absolut=True):

    # Den Fall bearbeiten wenn der String länger als 5 ist

    try:
        if absolut:
            return abs(float(str_number.replace(",", ".")))
        return float(str_number.replace(",", "."))
    
    except ValueError as err:
        return str(err)


def sum_kewords(keywords: dict, row: list[str]):

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

    keywords = {'Lebensmittel': ["markt der prinz", "rewe", "lidl", "aldi", 
                                 "netto", "polonia", "tegut", "edeka", 
                                 "SUDE MARKET"]}
    
    res_rows = []
    bilanz = {"Einnahmen": 0, "Ausgaben": 0, "Bilanz": 0}

    with open('Kontoumsaetze_Juli_2024.csv') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=';')
        
        for row in spamreader:
            res = sum_kewords(keywords, row)
            res_rows.append(res)
            bil = do_bilanzierung(row)
            
            if isinstance(bil, float):
                if bil < 0:
                    bilanz["Ausgaben"] += bil
                elif bil > 0:
                    bilanz["Einnahmen"] += bil
            
    bilanz["Bilanz"] = bilanz["Einnahmen"] + bilanz["Ausgaben"]
    print(bilanz)
