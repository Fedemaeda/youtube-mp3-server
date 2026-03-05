import yt_dlp
import requests

URL = "https://www.youtube.com/watch?v=P2JNhprE9Ho"

def test(name, opts):
    print(f"\n--- {name} ---")
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.extract_info(URL, download=False)
            print("SUCCESS")
            return True
    except Exception as e:
        print(f"FAIL: {str(e)[:150]}")
        return False

# Test 1: Web Music
test("web_music", {
    'simulate': True,
    'quiet': False,
    'extractor_args': {'youtube': {'player_client': ['web_music']}}
})

# Test 2: iOS with specific version and skipping web
test("ios_skip_web", {
    'simulate': True,
    'quiet': False,
    'extractor_args': {
        'youtube': {
            'player_client': ['ios'],
            'player_skip': ['web', 'web_creator'],
            'ios_ver': ['19.45.4']
        }
    }
})

# Test 3: Android with specific version
test("android_skip_web", {
    'simulate': True,
    'quiet': False,
    'extractor_args': {
        'youtube': {
            'player_client': ['android'],
            'player_skip': ['web', 'web_creator'],
            'android_ver': ['19.45.4']
        }
    }
})

# Test 4: TV Embedded (native)
test("tv_embedded", {
    'simulate': True,
    'quiet': False,
    'extractor_args': {'youtube': {'player_client': ['tv_embedded']}}
})
