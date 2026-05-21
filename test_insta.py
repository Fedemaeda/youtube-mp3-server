import yt_dlp
import sys

ydl_opts = {
    'quiet': False,
    'verbose': True,
    'nocheckcertificate': True,
    'prefer_insecure': True,
}

url = "https://ddinstagram.com/reel/C-K8iI0NxWp/"

try:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        print("Success!")
        print(info.get('title'))
except Exception as e:
    print("Error:", e)
