#!/usr/bin/env python3
"""
Test yt-dlp PO token configuration for 2026 - correct syntax
"""
import yt_dlp
import requests
import sys
import os

TEST_URL = 'https://www.youtube.com/watch?v=P2JNhprE9Ho'

# Get PO token from bgutil
try:
    r = requests.post('http://127.0.0.1:4416/get_pot', json={}, timeout=30)
    d = r.json()
    pot = d.get('poToken')
    visitor = d.get('contentBinding')
    print(f"POT: {pot[:30] if pot else None}...")
    print(f"Visitor: {visitor[:30] if visitor else None}...")
except Exception as e:
    print(f"POT fetch failed: {e}")
    pot, visitor = None, None

BASE_OPTS = {
    'outtmpl': '/tmp/test_%(id)s.%(ext)s',
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': False,
    'nocheckcertificate': True,
    'socket_timeout': 60,
    'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '128'}],
}

def test(name, opts):
    print(f"\n{'='*60}\nTEST: {name}\n{'='*60}")
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(TEST_URL, download=True)
            title = info.get('title', 'unknown')
            print(f"  SUCCESS: {title}")
            return True
    except Exception as e:
        msg = str(e)[:200]
        print(f"  FAIL: {msg}")
        return False

# Test 1: PO token with WEB client (correct 2026 syntax)
if pot:
    opts = {
        **BASE_OPTS,
        'extractor_args': {
            'youtube': {
                'player_client': ['web'],
                'po_token': [f'web+{pot}'],
            }
        },
    }
    if visitor:
        opts['extractor_args']['youtube']['visitor_data'] = [visitor]
    if test("web client + PO token (correct syntax)", opts):
        print("WINNER: web + POT"); sys.exit(0)

# Test 2: WEB_EMBEDDED (tv embedded correct name)
if pot:
    opts = {
        **BASE_OPTS,
        'extractor_args': {
            'youtube': {
                'player_client': ['web_embedded'],
                'po_token': [f'web_embedded+{pot}'],
            }
        },
    }
    if visitor:
        opts['extractor_args']['youtube']['visitor_data'] = [visitor]
    if test("web_embedded client + PO token", opts):
        print("WINNER: web_embedded + POT"); sys.exit(0)

# Test 3: IOS only (mobile clients need NO po_token in 2026)
opts = {
    **BASE_OPTS,
    'extractor_args': {'youtube': {'player_client': ['ios']}},
}
if test("ios only (no POT)", opts):
    print("WINNER: ios only"); sys.exit(0)

# Test 4: android only
opts = {
    **BASE_OPTS,
    'extractor_args': {'youtube': {'player_client': ['android']}},
}
if test("android only (no POT)", opts):
    print("WINNER: android only"); sys.exit(0)

# Test 5: mweb only
opts = {
    **BASE_OPTS,
    'extractor_args': {'youtube': {'player_client': ['mweb']}},
}
if test("mweb only (no POT)", opts):
    print("WINNER: mweb only"); sys.exit(0)

# Test 6: IOS with POT
if pot:
    opts = {
        **BASE_OPTS,
        'extractor_args': {
            'youtube': {
                'player_client': ['ios'],
                'po_token': [f'ios+{pot}'],
            }
        },
    }
    if visitor:
        opts['extractor_args']['youtube']['visitor_data'] = [visitor]
    if test("ios + POT", opts):
        print("WINNER: ios + POT"); sys.exit(0)

# Test 7: android_testsuite (less restricted client)
opts = {
    **BASE_OPTS,
    'extractor_args': {'youtube': {'player_client': ['android_testsuite']}},
}
if test("android_testsuite (no POT)", opts):
    print("WINNER: android_testsuite"); sys.exit(0)

# Test 8: ALL clients with POT on all
if pot:
    token_list = [f'web+{pot}', f'ios+{pot}', f'android+{pot}', f'mweb+{pot}']
    opts = {
        **BASE_OPTS,
        'extractor_args': {
            'youtube': {
                'player_client': ['web', 'ios', 'android', 'mweb'],
                'po_token': token_list,
            }
        },
    }
    if visitor:
        opts['extractor_args']['youtube']['visitor_data'] = [visitor]
    if test("all clients + all POT", opts):
        print("WINNER: all+POT"); sys.exit(0)

# Test 9: List all available clients from yt-dlp source
print("\n\nAvailable clients in this yt-dlp version:")
try:
    from yt_dlp.extractor.youtube import YoutubeIE
    if hasattr(YoutubeIE, '_SUPPORTED_CLIENTS'):
        print(list(YoutubeIE._SUPPORTED_CLIENTS.keys()))
    elif hasattr(YoutubeIE, '_INNERTUBE_CLIENTS'):
        print(list(YoutubeIE._INNERTUBE_CLIENTS.keys()))
except:
    pass

print("\nAll tests FAILED.")
sys.exit(1)
