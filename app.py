import os
import uuid
import requests
from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
import yt_dlp
import logging
import socket
import re
import traceback
import random
import glob
import shutil
import unicodedata
from urllib.parse import urlparse

app = Flask(__name__)
app.logger.setLevel(logging.INFO)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_FOLDER = os.path.join(BASE_DIR, 'downloads')
COOKIES_FILE = os.path.join(BASE_DIR, 'cookies.txt')
PROXY_URL = os.environ.get('PROXY_URL', '')
POT_PROVIDER_URL = os.environ.get('POT_PROVIDER_URL', 'http://127.0.0.1:4416')

if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

import concurrent.futures

def log_startup_info():
    try:
        import yt_dlp
        app.logger.info(f"YT-DLP Version: {yt_dlp.version.__version__}")
        app.logger.info(f"Proxy URL: {PROXY_URL or 'None'}")
        app.logger.info(f"POT Provider: {POT_PROVIDER_URL}")
    except: pass

def get_residential_proxy():
    """Fetch and verify free HTTP proxies by confirming they successfully mask the IP."""
    try:
        urls = [
             "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
             "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4.txt",
             "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt",
             "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
             "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks5.txt",
             "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
             "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt",
             "https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt"
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
    """Fetch a PO token from the bgutil sidecar (optional)."""
    pot_url = POT_PROVIDER_URL
    if not pot_url:
        app.logger.info("No POT_PROVIDER_URL configured, skipping PO token.")
        return None, None
    try:
        app.logger.info(f"Fetching PO Token from {pot_url}...")
        resp = requests.post(f"{pot_url}/get_pot", json={}, timeout=3)
        if resp.status_code == 200:
            data = resp.json()
            token = data.get('poToken') or data.get('po_token') or data.get('potoken')
            visitor = data.get('contentBinding') or data.get('visitorData')
            return token, visitor
    except: pass
    return None, None


def validate_supported_url(raw_url):
    if not raw_url:
        return False, 'URL required'
    try:
        parsed = urlparse(raw_url.strip())
    except Exception:
        return False, 'Invalid URL format'

    if parsed.scheme not in ('http', 'https') or not parsed.netloc:
        return False, 'Invalid URL format. Use a full http(s) URL.'

    host = parsed.netloc.lower()
    path = (parsed.path or '').lower()

    if 'youtube.com' in host or 'youtu.be' in host:
        return True, None

    if 'x.com' in host or 'twitter.com' in host:
        if '/status/' not in path:
            return False, 'For X/Twitter, use a post URL containing /status/.'
        return True, None

    if 'instagram.com' in host:
        valid_prefixes = ('/p/', '/reel/', '/reels/', '/tv/')
        if not any(path.startswith(prefix) for prefix in valid_prefixes):
            return False, 'For Instagram, use a post/reel URL (p, reel, reels, or tv).'
        return True, None

    return False, 'Unsupported URL. Supported: YouTube, X/Twitter, Instagram.'


def sanitize_download_stem(title, fallback='media', max_length=80):
    if not title:
        return fallback

    normalized = unicodedata.normalize('NFKD', str(title))
    ascii_title = normalized.encode('ascii', 'ignore').decode('ascii')
    ascii_title = re.sub(r'https?://\S+', ' ', ascii_title)
    ascii_title = re.sub(r'[\\/*?:"<>|]', ' ', ascii_title)
    ascii_title = re.sub(r'[^A-Za-z0-9._()\- ]+', ' ', ascii_title)
    ascii_title = re.sub(r'\s+', ' ', ascii_title).strip(' ._-')

    if not ascii_title:
        return fallback

    return ascii_title[:max_length].rstrip(' ._-') or fallback


def build_youtube_attempts(has_cookies):
    if has_cookies:
        return [
            {'clients': ['tv'], 'allow_missing_pot': True, 'use_cookies': True},
            {'clients': ['web_safari'], 'allow_missing_pot': True, 'use_cookies': True},
            {'clients': ['mweb'], 'use_cookies': True, 'fetch_po_token': True},
            {'clients': ['android'], 'use_cookies': False, 'fetch_po_token': True},
            {'clients': ['ios'], 'use_cookies': False, 'fetch_po_token': True},
        ]

    return [
        {'clients': ['android'], 'use_cookies': False, 'fetch_po_token': True},
        {'clients': ['ios'], 'use_cookies': False, 'fetch_po_token': True},
        {'clients': ['web_safari'], 'allow_missing_pot': True, 'use_cookies': False},
        {'clients': ['mweb'], 'use_cookies': False, 'fetch_po_token': True},
    ]


@app.route('/api/validate-url', methods=['POST'])
def validate_url():
    data = request.get_json() or {}
    url = data.get('url', '')
    ok, error = validate_supported_url(url)
    if not ok:
        return jsonify({'valid': False, 'error': error}), 400
    return jsonify({'valid': True})

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

@app.route('/api/sync-cookies-json', methods=['POST'])
def sync_cookies_json():
    try:
        data = request.get_json()
        if not data or 'cookies' not in data:
            return jsonify({'error': 'No cookies provided'}), 400
        
        cookies = data['cookies']
        netscape_lines = [
            "# Netscape HTTP Cookie File",
            "# This file was generated by StreamRip Extension",
            ""
        ]
        
        for c in cookies:
            domain = c.get('domain', '')
            flag = "TRUE" if domain.startswith('.') else "FALSE"
            path = c.get('path', '/')
            secure = "TRUE" if c.get('secure') else "FALSE"
            expiration = int(c.get('expirationDate', 0))
            name = c.get('name', '')
            value = c.get('value', '')
            
            line = f"{domain}\t{flag}\t{path}\t{secure}\t{expiration}\t{name}\t{value}"
            netscape_lines.append(line)
        
        with open(COOKIES_FILE, 'w', encoding='utf-8') as f:
            f.write('\n'.join(netscape_lines) + '\n')
            
        app.logger.info(f"Synchronized {len(cookies)} cookies from extension.")
        return jsonify({'success': True, 'count': len(cookies)})
    except Exception as e:
        app.logger.error(f"Cookie sync error: {e}")
        return jsonify({'error': str(e)}), 500

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

        ok, validation_error = validate_supported_url(url)
        if not ok:
            return jsonify({'error': validation_error}), 400

        is_youtube = 'youtube.com' in url or 'youtu.be' in url
        is_instagram = 'instagram.com' in url
        unique_id = str(uuid.uuid4())
        # Use a filesystem-safe temporary name and set the user-facing filename later.
        output_template = os.path.join(DOWNLOAD_FOLDER, f'{unique_id}.%(ext)s')

        ffmpeg_path = os.path.join(BASE_DIR, 'ffmpeg.exe')
        ydl_opts = {
            'outtmpl': output_template,
            'format': 'bestaudio/best' if target_format == 'mp3' else 'bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'noplaylist': True, 'quiet': False, 'verbose': True, 'nocheckcertificate': True, 'prefer_insecure': True, 'socket_timeout': 30,
            'ffmpeg_location': ffmpeg_path if os.path.exists(ffmpeg_path) else 'ffmpeg',
            'windowsfilenames': True,
        }
        if target_format == 'mp3':
            ydl_opts['postprocessors'] = [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}]
        elif target_format == 'mp4': ydl_opts['merge_output_format'] = 'mp4'

        has_cookie_file = os.path.exists(COOKIES_FILE)
        youtube_attempts = build_youtube_attempts(has_cookie_file) if is_youtube else []
        attempts = len(youtube_attempts) if youtube_attempts else 3
        last_error = ""
        downloaded_file, info = None, None
        success = False

        for attempt in range(attempts):
            app.logger.info(f"Download attempt {attempt+1}/{attempts}")
            if is_youtube:
                strategy = youtube_attempts[attempt]
                current_clients = strategy['clients']
                app.logger.info(f"Using player_client: {current_clients}")
                # Update bypass clients
                ydl_opts['extractor_args'] = {'youtube': {
                    'player_client': current_clients,
                    'player_skip': ['web', 'web_creator']
                }}
                if strategy.get('allow_missing_pot'):
                    ydl_opts['extractor_args']['youtube']['formats'] = ['missing_pot']
                # Try direct connection first, only use proxies on retries
                proxy = None
                if attempt > 0:
                    proxy = get_residential_proxy()
                
                if proxy:
                    ydl_opts['proxy'] = proxy
                    app.logger.info(f"Trying with proxy: {proxy}")
                    # Remove PO token when using proxy (IP binding mismatch)
                    ydl_opts['extractor_args']['youtube'].pop('po_token', None)
                    ydl_opts['extractor_args']['youtube'].pop('visitor_data', None)
                else:
                    if strategy.get('fetch_po_token'):
                        app.logger.info("Direct connection - fetching PO Token if available")
                        pot, visitor = get_po_token()
                        if pot:
                            tokens = [f"{c}+{pot}" for c in current_clients if c not in ['android', 'android_testsuite']]
                            if tokens:
                                ydl_opts['extractor_args']['youtube']['po_token'] = tokens
                            if visitor:
                                ydl_opts['extractor_args']['youtube']['visitor_data'] = [visitor]
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
            
            # Use a temporary copy of the cookie file so yt-dlp doesn't overwrite and ruin the original on failure
            temp_cookie_file = None
            use_cookie_file = has_cookie_file and (not is_youtube or strategy.get('use_cookies', True))
            if use_cookie_file:
                temp_cookie_file = os.path.join(DOWNLOAD_FOLDER, f'cookies_{unique_id}_{attempt}.txt')
                shutil.copy2(COOKIES_FILE, temp_cookie_file)
                ydl_opts['cookiefile'] = temp_cookie_file
                
            if is_instagram: ydl_opts['http_headers'] = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

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
                        success = True
                        break
            except Exception as e:
                last_error = str(e)
                app.logger.warning(f"Attempt failed: {last_error}")
                # Log more details on the error to see blocking patterns
                if "Sign in to confirm" in last_error or "not a bot" in last_error:
                    app.logger.error("Youtube still detecting us as bot with this proxy/setup.")
                elif "No video could be found in this tweet" in last_error:
                    last_error = "That X/Twitter post does not contain downloadable video/audio."
                    break
                elif "Instagram sent an empty media response" in last_error or "Instagram API is not granting access" in last_error:
                    last_error = "Instagram blocks anonymous downloads. Please upload cookies.txt containing Instagram logged-in cookies via the web interface."
                    app.logger.error(last_error)
                    break # Don't retry since it's a hard auth block
                
                # If it's a permanent error (not a proxy/bot detect), don't bother retrying 
                # (unless it's a proxy error, then we *do* want to retry with a different proxy)
                if "ProxyError" not in last_error and "403" not in last_error and "timed out" not in last_error and "reset by peer" not in last_error:
                     # e.g. "Video unavailable" or "Invalud URL"
                     if "bot" not in last_error: break
            finally:
                if temp_cookie_file and os.path.exists(temp_cookie_file):
                    try:
                        os.remove(temp_cookie_file)
                    except: pass
        else: 
            return jsonify({'error': f'Failed after {attempts} attempts. Last: {last_error}'}), 500

        if not success:
            if not last_error:
                last_error = "The URL could not be downloaded. Check that the link is public and valid."
            return jsonify({'error': last_error}), 500

        # Success handling
        if not info:
             return jsonify({'error': 'Download succeeded but no metadata was returned.'}), 500
             
        original_title = info.get('title', 'video')
        clean_title = sanitize_download_stem(original_title, fallback='video')
        download_name = f"{clean_title}.{target_format}"
        mimetype = 'video/mp4' if target_format == 'mp4' else 'audio/mpeg'
        
        if not downloaded_file or not os.path.exists(downloaded_file):
             return jsonify({'error': 'File was downloaded but could not be located on disk.'}), 500

        response = send_file(downloaded_file, as_attachment=True, download_name=download_name, mimetype=mimetype)
        response.headers['X-Download-Filename'] = download_name

        @response.call_on_close
        def remove_file():
            try:
                if downloaded_file and os.path.exists(downloaded_file):
                    os.remove(downloaded_file)
            except Exception:
                pass

        return response
    except Exception as e:
        app.logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    response.headers['Access-Control-Expose-Headers'] = 'Content-Disposition, X-Download-Filename'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    return response

if __name__ == '__main__':
    log_startup_info()
    port = int(os.environ.get('PORT', 5005))
    app.run(host='0.0.0.0', port=port)
