import requests

r = requests.get('http://192.168.43.200:3000/api/courses')

print(r.json())