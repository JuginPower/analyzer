import csv
import re


keywords = {'Lebensmittel': ["markt der prinz", "rewe", "lidl", "aldi", "netto",
                             "polonia", "tegut", "edeka"]}

summe_lebensmittel = 0

with open('Kontoumsaetze_Juli_2024.csv') as csvfile:
    spamreader = csv.reader(csvfile, delimiter=';')
    custom_row = []
    
    for row in spamreader:
        for item in keywords.items():
            kategorie = item[0]
            for value in item[1]:
                try:
                    if re.search(value, row[3] + row[4], re.IGNORECASE):
                        soll = abs(float(row[-3].replace(",", ".")))
                        summe_lebensmittel += soll
                except IndexError:
                    print("Index Error hier:", row)
            

print("Summe Lebensmittel:", round(summe_lebensmittel, 2))
