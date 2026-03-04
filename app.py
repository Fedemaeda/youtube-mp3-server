import os
import uuid
import requests
from flask import Flask, request, jsonify, render_template, send_file, after_this_request
from flask_cors import CORS
import yt_dlp

import logging

app = Flask(__name__)
app.logger.setLevel(logging.INFO)
CORS(app)  # Allow cross-origin requests from the Chrome Extension
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_FOLDER = os.path.join(BASE_DIR, 'downloads')
COOKIES_FILE = os.path.join(BASE_DIR, 'cookies.txt')
POT_PROVIDER_URL = os.environ.get('POT_PROVIDER_URL')
PROXY_URL = os.environ.get('PROXY_URL', 'socks5://host.docker.internal:40000')

def is_proxy_reachable(proxy_url):
    """Check if the SOCKS5 proxy is reachable."""
    import socket
    try:
        # Extract host and port from proxy_url
        parts = proxy_url.split('://')[-1].split(':')
        host = parts[0]
        port = int(parts[1])
        with socket.create_connection((host, port), timeout=2):
            return True
    except Exception:
        return False
    return False

def get_po_token():
    """Fetch a PO token from the bgutil sidecar service or environment."""
    # Try environment variable first (manual override)
    po_token = os.environ.get('PO_TOKEN')
    if po_token:
        visitor_data = os.environ.get('VISITOR_DATA')
        return po_token, visitor_data

    # Try bgutil sidecar service (checking multiple potential key formats)
    pot_url = os.environ.get('POT_PROVIDER_URL', 'http://127.0.0.1:4416')
    try:
        app.logger.info(f"Fetching PO Token from {pot_url}/get_pot...")
        resp = requests.post(f"{pot_url}/get_pot", json={}, timeout=60)
        app.logger.info(f"POT provider status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            # Various bgutil versions use different field names
            token = data.get('poToken') or data.get('po_token') or data.get('potoken')
            visitor = data.get('contentBinding') or data.get('visitor_data') or data.get('visit_identifier') or data.get('visitorData')
            app.logger.info(f"POT found: {'Yes' if token else 'No'}, Visitor found: {'Yes' if visitor else 'No'}")
            return token, visitor
        else:
            app.logger.warning(f"POT provider returned error: {resp.text}")
    except Exception as e:
        app.logger.warning(f"Could not reach bgutil pot provider: {e}")

    return None, None

if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/upload-cookies', methods=['POST'])
def upload_cookies():
    """Endpoint to upload a YouTube cookies.txt file for bot bypass."""
    if 'cookies' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    f = request.files['cookies']
    if f.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    f.save(COOKIES_FILE)
    return jsonify({'success': True, 'message': 'Cookies uploaded successfully!'})

@app.route('/api/cookies-status', methods=['GET'])
def cookies_status():
    """Check if a cookies file has been uploaded."""
    exists = os.path.exists(COOKIES_FILE)
    return jsonify({'has_cookies': exists})

@app.route('/api/download-extension')
def download_extension():
    """Endpoint to download the Chrome extension ZIP file."""
    extension_path = os.path.join(BASE_DIR, 'extension.zip')
    if os.path.exists(extension_path):
        return send_file(
            extension_path,
            as_attachment=True,
            download_name='StreamRip_Extension.zip',
            mimetype='application/zip'
        )
    return jsonify({'error': 'Extension file not found'}), 404

@app.route('/api/download', methods=['POST', 'GET'])
def download():
    if request.method == 'POST':
        data = request.get_json() or {}
        url = data.get('url')
        target_format = data.get('format', 'mp3')
    else:
        url = request.args.get('url')
        target_format = request.args.get('format', 'mp3')

    if not url:
        return jsonify({'error': 'URL is required'}), 400

    is_youtube = 'youtube.com' in url or 'youtu.be' in url
    unique_id = str(uuid.uuid4())
    output_template = os.path.join(DOWNLOAD_FOLDER, f'%(title)s_{unique_id}.%(ext)s')

    ydl_opts = {
        'outtmpl': output_template,
        'format': 'bestaudio/best' if target_format == 'mp3' else 'bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'noplaylist': True,
        'quiet': False,
        'verbose': True,
        'nocheckcertificate': True,
        'prefer_insecure': True,
        'allow_unsecure_tools': True,
        'sleep_interval_requests': 2,
        'socket_timeout': 60,
        'ignoreerrors': False,
    }

    if target_format == 'mp3':
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    elif target_format == 'mp4':
        ydl_opts['merge_output_format'] = 'mp4'

    # Proxy logic
    if os.environ.get('FLASK_ENV') == 'production':
        if is_proxy_reachable(PROXY_URL):
            app.logger.info(f"Using proxy: {PROXY_URL}")
            ydl_opts['proxy'] = PROXY_URL
        else:
            app.logger.warning("Proxy is unreachable. Falling back to direct connection.")
    else:
        app.logger.info("Running in development mode, no proxy used.")

    # YouTube-specific bypass configurations
    if is_youtube:
        # Prioritize mobile clients (ios, mweb, android) which are less affected by datacenter blocks
        # 'mweb' is particularly good for avoiding the "Sign in to confirm you're not a bot" screen.
        ydl_opts['extractor_args'] = {
            'youtube': {
                'player_client': ['ios', 'mweb', 'android', 'tv', 'web'],
                'player_skip': ['web_creator'],
                'jsc': ['deno'],
                # Specific version strings to look like real apps
                'ios_ver': ['19.45.4', '17.33.2', '16.5'],
                'android_ver': ['19.45.4', '17.33.2'],
            }
        }
        
        # Enable remote components for EJS
        ydl_opts['remote_components'] = ['ejs:github']

        # Fetch PO Token from bgutil sidecar (bypasses 'Sign in to confirm not a bot')
        po_token, visitor_data = get_po_token()
        if po_token:
            app.logger.info(f"Using PO Token: {po_token[:10]}...")
            # For 2025+, mapping the same token to all clients is the most successful approach
            token_list = [
                f'web+{po_token}', 
                f'mweb+{po_token}',
                f'ios+{po_token}', 
                f'android+{po_token}',
                f'tv+{po_token}'
            ]
            ydl_opts['extractor_args']['youtube']['po_token'] = token_list
            
            if visitor_data:
                # Visitor data must match or be associated with the token generator
                ydl_opts['extractor_args']['youtube']['visitor_data'] = [visitor_data]
        
        # Use cookies if available
        if os.path.exists(COOKIES_FILE):
            app.logger.info("Cookies file found, attaching to ydl_opts")
            ydl_opts['cookiefile'] = COOKIES_FILE
        else:
            app.logger.warning("No cookies found. Datacenter IPs (Oracle) will likely be blocked without cookies.")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            downloaded_file = ydl.prepare_filename(info)
            if target_format == 'mp3':
                base, _ = os.path.splitext(downloaded_file)
                downloaded_file = base + '.mp3'

        if not os.path.exists(downloaded_file):
            return jsonify({'error': f'Failed to generate {target_format} file'}), 500

        # Memory efficient sending and automatic cleanup
        import re
        # Get the original title from metadata
        original_title = info.get('title', 'video')
        # Remove only truly illegal filesystem characters, preserve spaces/accents
        clean_title = re.sub(r'[\\/*?:"<>|]', '', original_title)
        # Clean up whitespace but keep single spaces
        clean_title = ' '.join(clean_title.split()).strip()
        # Final safety check and length limit
        clean_title = clean_title if clean_title else f'video_{unique_id[:8]}'
        download_name = f"{clean_title[:150]}.{target_format}"

        mimetype = 'video/mp4' if target_format == 'mp4' else 'audio/mpeg'
        
        # Schedule file deletion after the response is sent
        @after_this_request
        def remove_file(response):
            try:
                if os.path.exists(downloaded_file):
                    os.remove(downloaded_file)
            except Exception as e:
                app.logger.error(f"Error removing file {downloaded_file}: {e}")
            return response

        return send_file(
            downloaded_file,
            as_attachment=True,
            download_name=download_name,
            mimetype=mimetype
        )

    except Exception as e:
        import traceback
        error_msg = str(e)
        app.logger.error(f"Download error: {error_msg}")
        app.logger.error(traceback.format_exc())
        
        # Cleanup file if it exists despite the error
        try:
            # We don't have downloaded_file yet here if it failed early, but we can try to find it
            pass 
        except:
            pass

        # User-friendly error for bot detection
        if "Sign in to confirm you're not a bot" in error_msg or "confirm you're not a bot" in error_msg:
            return jsonify({
                'error': 'YouTube detected a bot challenge. Please upload fresh cookies via the Authentication tab.',
                'code': 'BOT_DETECTION'
            }), 403
        
        if "Requested format is not available" in error_msg:
            return jsonify({
                'error': 'Requested format not available. YouTube might be blocking the server IP. Try refreshing cookies or checking the server logs.',
                'code': 'FORMAT_UNAVAILABLE'
            }), 400

        return jsonify({'error': error_msg}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
