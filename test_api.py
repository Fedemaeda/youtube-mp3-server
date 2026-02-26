import requests

url = "http://144.22.61.82:5000/api/download"
payload = {"url": "https://www.youtube.com/watch?v=bW9JIcXyCaA"}

try:
    print(f"Testing {url}...")
    response = requests.post(url, json=payload, timeout=60)
    print(f"Status Code: {response.status_code}")
    print(f"Content-Type: {response.headers.get('Content-Type')}")
    if response.status_code == 200:
        print("Success! The server returned a valid response.")
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Request failed: {e}")
