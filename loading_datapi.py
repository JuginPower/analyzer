import requests
from requests.auth import HTTPBasicAuth
from classes import BaseLoader
from settings import datapi_url, datapi_username, datapi_passwd
import logging

"""
1. Wenn die frischen Daten da sind nochmal neu alles testen. Und nicht vergessen die Preise in der Datenbank alle vorher 
   zu löschen.
"""

logger = logging.getLogger(__name__)
logging.basicConfig(filename="loading_datapi.log", encoding="utf-8", level=logging.ERROR,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d, %H:%M:%S')

loader = BaseLoader()
res = requests.get(datapi_url, auth=HTTPBasicAuth(datapi_username, datapi_passwd))

if 299 >= res.status_code >= 200:
    data_source = res.json()
    try:
        result = loader.upload(data_source)
    except Exception as err:
        logger.error("Something goes wrong in loading_datapi: %s", err)
        raise err
    else:
        print("Result from upload from api:", result)
        res = requests.delete(datapi_url, auth=HTTPBasicAuth(datapi_username, datapi_passwd))
        print("Status Code from DELETE request:", res.status_code)

elif not (299 >= res.status_code >= 200):
    print(f"Status Code: {res.status_code} occured!")
