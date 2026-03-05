import os
import uuid
import requests
from flask import Flask, request, jsonify, render_template, send_file, after_this_request
from flask_cors import CORS
import yt_dlp
import logging
import socket
import re
import traceback
import random
import glob

app = Flask(__name__)
app.logger.setLevel(logging.INFO)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_FOLDER = os.path.join(BASE_DIR, 'downloads')
COOKIES_FILE = os.path.join(BASE_DIR, 'cookies.txt')
PROXY_URL = os.environ.get('PROXY_URL', 'socks5://host.docker.internal:40000')

if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

import concurrent.futures

def get_residential_proxy():
    """Fetch and verify free HTTP proxies by confirming they successfully mask the IP."""
    try:
        urls = [
             "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
             "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt",
             "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
             "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks5.txt",
             "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
             "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt"
        ]
        
        all_proxies = []
        for u in urls:
            try:
                r = requests.get(u, timeout=10)
                ptype = "socks5" if "socks5" in u else "http"
                all_proxies.extend([(ptype, p.strip()) for p in r.text.splitlines() if p.strip()])
            except: pass
            
        random.shuffle(all_proxies)
        
        def check_proxy(proxy_info):
            ptype, p = proxy_info
            proxy_url = f"{ptype}://{p}"
            try:
                # Check actual YouTube access - generate_204 is fast and reliable
                r = requests.get('https://www.youtube.com/generate_204', 
                                 proxies={'http': proxy_url, 'https': proxy_url}, 
                                 timeout=4)
                if r.status_code == 204:
                    return proxy_url
            except: pass
            return None

        app.logger.info("Searching for a working YouTube proxy...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            # Test more candidates to be sure
            futures = {executor.submit(check_proxy, p): p for p in all_proxies[:500]}
            for future in concurrent.futures.as_completed(futures):
                res = future.result()
                if res:
                    executor.shutdown(wait=False, cancel_futures=True)
                    return res
    except Exception as e:
        app.logger.warning(f"Proxy search error: {e}")
    return None

def get_po_token():
    """Fetch a PO token from the bgutil sidecar."""
    pot_url = os.environ.get('POT_PROVIDER_URL', 'http://127.0.0.1:4416')
    try:
        app.logger.info(f"Fetching PO Token from {pot_url}...")
        resp = requests.post(f"{pot_url}/get_pot", json={}, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            token = data.get('poToken') or data.get('po_token') or data.get('potoken')
            visitor = data.get('contentBinding') or data.get('visitorData')
            return token, visitor
    except: pass
    return None, None



@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/upload-cookies', methods=['POST'])
def upload_cookies():
    if 'cookies' not in request.files: return jsonify({'error': 'No file uploaded'}), 400
    f = request.files['cookies']
    f.save(COOKIES_FILE)
    return jsonify({'success': True, 'message': 'Cookies uploaded successfully!'})

@app.route('/api/cookies-status', methods=['GET'])
def cookies_status():
    return jsonify({'has_cookies': os.path.exists(COOKIES_FILE)})

@app.route('/api/download-extension')
def download_extension():
    extension_path = os.path.join(BASE_DIR, 'extension.zip')
    if os.path.exists(extension_path):
        return send_file(extension_path, as_attachment=True, download_name='StreamRip_Extension.zip', mimetype='application/zip')
    return jsonify({'error': 'Not found'}), 404

@app.route('/api/download', methods=['POST', 'GET'])
def download():
    try:
        if request.method == 'POST':
            data = request.get_json() or {}
            url, target_format = data.get('url'), data.get('format', 'mp3')
        else:
            url, target_format = request.args.get('url'), request.args.get('format', 'mp3')

        if not url: return jsonify({'error': 'URL required'}), 400

        is_youtube = 'youtube.com' in url or 'youtu.be' in url
        is_instagram = 'instagram.com' in url
        unique_id = str(uuid.uuid4())
        output_template = os.path.join(DOWNLOAD_FOLDER, f'%(title)s_{unique_id}.%(ext)s')

        ydl_opts = {
            'outtmpl': output_template,
            'format': 'bestaudio/best' if target_format == 'mp3' else 'bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'noplaylist': True, 'quiet': False, 'verbose': True, 'nocheckcertificate': True, 'prefer_insecure': True, 'socket_timeout': 60,
            'remote_components': ['ejs:github'], 'extractor_args': {'youtube': {'jsc': ['deno']}}
        }
        if target_format == 'mp3':
            ydl_opts['postprocessors'] = [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}]
        elif target_format == 'mp4': ydl_opts['merge_output_format'] = 'mp4'

        attempts = 5
        last_error = ""
        downloaded_file, info = None, None

        # Different client strategies to rotate through if one is blocked
        client_combinations = [
            ['android'],         # Seems to work best without POT right now
            ['ios', 'android'],
            ['tv', 'mweb'],
            ['web_embedded'],
            ['android_testsuite']
        ]

        for attempt in range(attempts):
            app.logger.info(f"Download attempt {attempt+1}/{attempts}")
            if is_youtube:
                current_clients = client_combinations[attempt % len(client_combinations)]
                app.logger.info(f"Using player_client: {current_clients}")
                # Update bypass clients
                ydl_opts['extractor_args']['youtube'].update({
                    'player_client': current_clients,
                    'player_skip': ['web', 'web_creator']
                })
                # Decide proxy vs local IP (local IP needs PO Token)
                proxy = get_residential_proxy()
                if proxy:
                    ydl_opts['proxy'] = proxy
                    app.logger.info(f"Trying with proxy: {proxy}")
                    # Remove PO token when using proxy (IP binding mismatch)
                    ydl_opts['extractor_args']['youtube'].pop('po_token', None)
                    ydl_opts['extractor_args']['youtube'].pop('visitor_data', None)
                else:
                    app.logger.info("Direct connection - fetching PO Token")
                    pot, visitor = get_po_token()
                    if pot:
                        # Append POT for all rotated clients dynamically
                        tokens = [f"{c}+{pot}" for c in current_clients if c not in ['android', 'android_testsuite']]
                        if tokens:
                            ydl_opts['extractor_args']['youtube']['po_token'] = tokens
                        if visitor: ydl_opts['extractor_args']['youtube']['visitor_data'] = [visitor]
                    if os.environ.get('FLASK_ENV') == 'production' and PROXY_URL:
                        try:
                            # Verify if the main datacenter proxy works
                            r = requests.get('https://m.youtube.com', proxies={'http': PROXY_URL, 'https': PROXY_URL}, timeout=3)
                            if r.status_code == 200:
                                ydl_opts['proxy'] = PROXY_URL
                                app.logger.info(f"Using production proxy: {PROXY_URL}")
                        except: pass
            elif os.environ.get('FLASK_ENV') == 'production' and PROXY_URL:
                ydl_opts['proxy'] = PROXY_URL
            
            if os.path.exists(COOKIES_FILE): ydl_opts['cookiefile'] = COOKIES_FILE
            if is_instagram: ydl_opts['user_agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    if not info:
                        raise Exception("yt-dlp returned no info")
                    
                    rd = info.get('requested_downloads')
                    downloaded_file = rd[0]['filepath'] if rd and rd[0].get('filepath') else ydl.prepare_filename(info)
                    if target_format == 'mp3' and not downloaded_file.endswith('.mp3'):
                        base, _ = os.path.splitext(downloaded_file)
                        if os.path.exists(base + '.mp3'): downloaded_file = base + '.mp3'
                    
                    if os.path.exists(downloaded_file):
                        app.logger.info(f"Successfully downloaded: {downloaded_file}")
                        break
            except Exception as e:
                last_error = str(e)
                app.logger.warning(f"Attempt failed: {last_error}")
                # Log more details on the error to see blocking patterns
                if "Sign in to confirm" in last_error or "not a bot" in last_error:
                    app.logger.error("Youtube still detecting us as bot with this proxy/setup.")
                
                # If it's a permanent error (not a proxy/bot detect), don't bother retrying 
                # (unless it's a proxy error, then we *do* want to retry with a different proxy)
                if "ProxyError" not in last_error and "403" not in last_error and "timed out" not in last_error and "reset by peer" not in last_error:
                     # e.g. "Video unavailable" or "Invalud URL"
                     if "bot" not in last_error: break
        else: return jsonify({'error': f'Failed after {attempts} attempts. Last: {last_error}'}), 500

        # Success handling - info is guaranteed to be truthy due to the check above
        original_title = info.get('title', 'video')
        clean_title = re.sub(r'[\\/*?:"<>|]', '', original_title)[:100].strip()
        download_name = f"{clean_title}.{target_format}"
        mimetype = 'video/mp4' if target_format == 'mp4' else 'audio/mpeg'
        
        @after_this_request
        def remove_file(response):
            try:
                if downloaded_file and os.path.exists(downloaded_file): os.remove(downloaded_file)
            except: pass
            return response
        return send_file(downloaded_file, as_attachment=True, download_name=download_name, mimetype=mimetype)
    except Exception as e:
        app.logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000) # Gunicorn handles gunicorn, this is for dev
