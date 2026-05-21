
import yt_dlp
import os
import re
import uuid

def test_download():
    url = 'https://www.youtube.com/watch?v=jNQXAC9IVRw'
    target_format = 'mp3'
    unique_id = str(uuid.uuid4())
    DOWNLOAD_FOLDER = 'downloads'
    if not os.path.exists(DOWNLOAD_FOLDER):
        os.makedirs(DOWNLOAD_FOLDER)
    
    output_template = os.path.join(DOWNLOAD_FOLDER, f'%(title)s_{unique_id}.%(ext)s')
    
    # Matching the logic in app.py
    ydl_opts = {
        'outtmpl': output_template,
        'format': 'bestaudio/best',
        'noplaylist': True, 
        'quiet': False, 
        'verbose': True, 
        'nocheckcertificate': True, 
        'prefer_insecure': True, 
        'socket_timeout': 60,
    }
    
    if target_format == 'mp3':
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192'
        }]

    # Test with the first client in app.py logic
    current_clients = ['android']
    ydl_opts['extractor_args'] = {'youtube': {
        'player_client': current_clients,
        'player_skip': ['web', 'web_creator']
    }}

    print(f"Testing with clients: {current_clients}")
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            print("SUCCESS")
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    test_download()
