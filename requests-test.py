import requests

r = requests.get('http://localhost:3000/api/courses')

print(r.json())