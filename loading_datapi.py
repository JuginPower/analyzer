import requests
from requests.auth import HTTPBasicAuth
from classes import AdvancedLoader


url = "https://eugenkraft.com/stock"
username = "eugen"
passwd = "humax"
loader = AdvancedLoader()

res = requests.get(url, auth=HTTPBasicAuth(username, passwd))

if 299 >= res.status_code >= 200:
    data_source = res.json()
    result = loader.upload(data_source)
    print("Result from upload from api:", result)
    res = requests.delete(url, auth=HTTPBasicAuth(username, passwd))
    print("Status Code from DELETE request:", res.status_code)

elif not (299 > res.status_code >= 200):
    print(f"Status Code: {res.status_code} occured!")
