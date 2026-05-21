import requests
from bs4 import BeautifulSoup
import re

url = "https://www.instagram.com/reel/C-K8iI0NxWp/"

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://snapinsta.app/"
})

try:
    response = session.post("https://snapinsta.app/action.php", data={"url": url, "action": "post"}, timeout=10)
    print(response.status_code)
    print(response.text[:500])
except Exception as e:
    print("Error:", e)
