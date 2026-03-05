import yt_dlp
import requests
import sys

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

clients = ['tv', 'web', 'mweb', 'ios', 'android']

for client in clients:
    print(f"\n--- Testing Client: {client} ---")
    ydl_opts = {
        'simulate': True,
        'quiet': False,
        'nocheckcertificate': True,
        'remote_components': ['ejs:github'],
        'extractor_args': {
            'youtube': {
                'player_client': [client],
            }
        }
    }
    if pot:
        ydl_opts['extractor_args']['youtube']['po_token'] = [f"{client}+{pot}"]
    if visitor:
        ydl_opts['extractor_args']['youtube']['visitor_data'] = [visitor]
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(URL, download=False)
            print(f"SUCCESS with {client}!")
            # If we succeed with one, we might as well stop and use that
    except Exception as e:
        print(f"FAILED with {client}: {str(e)[:100]}")

print("\n--- Testing Client: web_embedded ---")
ydl_opts = {
    'simulate': True,
    'quiet': False,
    'extractor_args': {'youtube': {'player_client': ['web_embedded']}}
}
try:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.extract_info(URL, download=False)
        print("SUCCESS with web_embedded!")
except Exception as e:
    print(f"FAILED with web_embedded: {str(e)[:100]}")
