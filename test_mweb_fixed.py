import yt_dlp
import requests
import json
import sys

URL = "https://www.youtube.com/watch?v=P2JNhprE9Ho"

def get_pot():
    print("Fetching POT from bgutil...")
    try:
        r = requests.post('http://127.0.0.1:4416/get_pot', json={}, timeout=15)
        print(f"Status: {r.status_code}")
        data = r.json()
        pot = data.get('poToken')
        visitor = data.get('contentBinding')
        return pot, visitor
    except Exception as e:
        print(f"Error fetching POT: {e}")
        return None, None

pot, visitor = get_pot()

if not pot:
    print("FAILED: No PO token obtained.")
    sys.exit(1)

print(f"PO Token obtained: {pot[:30]}...")

# 2026 BEST BYPASS STRATEGY for Datacenter IPs:
# Use 'ios' client with a PO Token, but also skip 'web' to prevent fallback to restricted APIs.
ydl_opts = {
    'simulate': True,
    'quiet': False,
    'extractor_args': {
        'youtube': {
            'player_client': ['ios'],
            'po_token': [f"ios+{pot}"],
            'visitor_data': [visitor] if visitor else [],
            'player_skip': ['web', 'web_creator', 'mweb']
        }
    },
    'remote_components': ['ejs:github'],
    'js_runtimes': ['deno'],
}

print("\n--- Starting yt-dlp simulation ---")
try:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(URL, download=False)
        print(f"SUCCESS! Title: {info.get('title')}")
except Exception as e:
    print(f"FAILED: {e}")
