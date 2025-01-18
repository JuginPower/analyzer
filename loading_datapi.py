import requests
from requests.auth import HTTPBasicAuth
from classes import ApiLoader
import sqlite3
from settings import datapi_url, datapi_username, datapi_passwd


loader = ApiLoader()
res = requests.get(datapi_url, auth=HTTPBasicAuth(datapi_username, datapi_passwd))

if 299 >= res.status_code >= 200:
    data_source = res.json()
    try:
        result = loader.upload(data_source)
    except (KeyError, sqlite3.Error, IndexError) as err:
        raise err
    else:
        print("Result from upload from api:", result)
        res = requests.delete(datapi_url, auth=HTTPBasicAuth(datapi_username, datapi_passwd))
        print("Status Code from DELETE request:", res.status_code)

elif not (299 >= res.status_code >= 200):
    print(f"Status Code: {res.status_code} occured!")
