import csv
import re


def sum_kewords(keywords: dict, row: list[str]):

    """Diese Funktion gibt für jedes Keyword in einem Dictionary"""

    result = {}

    for item in keywords.items():
        kategorie: str = item[0]

        result[kategorie] = 0

        for value in item[1]:
            try:
                if re.search(value, row[3] + row[4], re.IGNORECASE):
                    soll = abs(float(row[-3].replace(",", ".")))
                    result[kategorie] += soll

            except IndexError as err:
                return str(err)
            
    return result


def do_bilanzierung(row: list):

    try:
        return row[15]
    except IndexError as err:
        return str(err)


if __name__ == "__main__":

    keywords = {'Lebensmittel': ["markt der prinz", "rewe", "lidl", "aldi", 
                                 "netto", "polonia", "tegut", "edeka", 
                                 "SUDE MARKET"]}
    
    res_rows = []

    with open('Kontoumsaetze_August_15.08.2024.csv') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=';')
        
        for row in spamreader:
            res = sum_kewords(keywords, row)
            res_rows.append(res)

            print(do_bilanzierung(row))
    