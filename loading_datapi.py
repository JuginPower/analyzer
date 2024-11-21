import requests
from requests.auth import HTTPBasicAuth
from classes import AdvancedLoader
from pathlib import Path
import os


BASE_DIR = Path(__file__).resolve().parent.parent
database_file = os.path.join(BASE_DIR, "finance.sqlite3")
url = "https://eugenkraft.com/stock"
username = "eugen"
passwd = "F9^q5(4lY:9}pm"
loader = AdvancedLoader(database_file)

res = requests.get(url, auth=HTTPBasicAuth(username, passwd))

if 299 > res.status_code >= 200:
    data_source = res.json()
    result = loader.upload(data_source)
    print("Result from upload from api:", result)

elif not (299 > res.status_code >= 200):
    raise ArithmeticError(f"Status Code: {res.status_code} occured!")

res = requests.delete(url, auth=HTTPBasicAuth(username, passwd))
print("Status Code from DELETE request:", res.status_code)
