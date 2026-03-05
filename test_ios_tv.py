import yt_dlp

URL = "https://www.youtube.com/watch?v=P2JNhprE9Ho"

ydl_opts = {
    'simulate': True,
    'quiet': False,
    'extractor_args': {
        'youtube': {
            'player_client': ['ios', 'tv'],
            'player_skip': ['web', 'web_creator', 'mweb'],
        }
    },
    'remote_components': ['ejs:github'],
}

try:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.extract_info(URL, download=False)
        print("SUCCESS with ios,tv skip web!")
except Exception as e:
    print(f"FAIL: {str(e)[:200]}")
