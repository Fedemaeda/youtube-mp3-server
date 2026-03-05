import yt_dlp

URL = "https://www.youtube.com/watch?v=P2JNhprE9Ho"

ydl_opts = {
    'simulate': True,
    'quiet': False,
    # Safari on macOS User Agent
    'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
    'extractor_args': {
        'youtube': {
            'player_client': ['web_safari'],
            'player_skip': ['web', 'web_creator', 'mweb', 'ios', 'tv', 'android'],
        }
    },
}

try:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.extract_info(URL, download=False)
        print("SUCCESS with web_safari impersonation!")
except Exception as e:
    print(f"FAIL: {str(e)[:200]}")
