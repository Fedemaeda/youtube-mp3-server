import yt_dlp
import requests

URL = "https://www.youtube.com/watch?v=P2JNhprE9Ho"

def get_pot():
    try:
        r = requests.post('http://127.0.0.1:4416/get_pot', json={}, timeout=10)
        return r.json()
    except:
        return {}

pot_data = get_pot()
pot = pot_data.get('poToken')
visitor = pot_data.get('contentBinding')

print(f"Using POT: {pot[:20]}...")

ydl_opts = {
    'simulate': True,
    'quiet': False,
    'extractor_args': {
        'youtube': {
            'player_client': ['mweb'],
            'po_token': [f"mweb+{pot}"],
            'visitor_data': [visitor]
        }
    },
    'remote_components': ['ejs:github'],
}

try:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.extract_info(URL, download=False)
        print("SUCCESS with mweb + POT!")
except Exception as e:
    print(f"FAIL: {str(e)[:200]}")
