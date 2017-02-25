import requests

BASE_URL = 'http://192.168.20.124:3000/api/'

def get():
    r = requests.get(BASE_URL + 'courses')
    print(r.json())

get()