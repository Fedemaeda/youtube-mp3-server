import requests

headers = {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
}
data = {
    'url': 'https://www.instagram.com/reel/C-K8iI0NxWp/'
}

try:
    response = requests.post('https://api.cobalt.tools/', headers=headers, json=data)
    print(response.status_code)
    print(response.json())
except Exception as e:
    print(e)
