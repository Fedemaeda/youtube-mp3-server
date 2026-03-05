import yt_dlp

URL = "https://www.youtube.com/watch?v=P2JNhprE9Ho"

ydl_opts = {
    'simulate': True,
    'quiet': False,
    'user_agent': 'com.google.android.youtube/19.45.4 (Linux; U; Android 14; en_US; Pixel 8 Pro; Build/UQ1A.231205.015) (gzip)',
    'extractor_args': {
        'youtube': {
            'player_client': ['android'],
            'player_skip': ['web', 'web_creator', 'mweb', 'ios', 'tv'],
        }
    },
}

try:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.extract_info(URL, download=False)
        print("SUCCESS with targeted android impersonation!")
except Exception as e:
    print(f"FAIL: {str(e)[:200]}")
