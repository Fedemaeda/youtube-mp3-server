import yt_dlp
import sys
import os

ydl_opts = {
    'quiet': False,
    'verbose': True,
    'nocheckcertificate': True,
    'prefer_insecure': True,
    'http_headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
}

if os.path.exists("cookies.txt"):
    ydl_opts['cookiefile'] = "cookies.txt"

url = "https://www.instagram.com/reel/C-K8iI0NxWp/"

try:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        print("Success!")
        print(info.get('title'))
except Exception as e:
    print("Error:", e)
