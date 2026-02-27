import os
import uuid
import requests
from flask import Flask, request, jsonify, render_template, send_file, after_this_request
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
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
    """Fetch a PO token from the environment or a sidecar service."""
    # Try environment variable first (manual override)
    po_token = os.environ.get('PO_TOKEN')
    if po_token:
        return po_token, None
        
    # Future: Add sidecar service call here
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
    return jsonify({'has_cookies': os.path.exists(COOKIES_FILE)})

@app.route('/api/download', methods=['POST', 'GET'])
def download():
    if request.method == 'POST':
        data = request.get_json()
        url = data.get('url') if data else None
    else:
        url = request.args.get('url')

    if not url:
        return jsonify({'error': 'URL is required'}), 400

    unique_id = str(uuid.uuid4())
    output_template = os.path.join(DOWNLOAD_FOLDER, f'%(title)s_{unique_id}.%(ext)s')

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': output_template,
        'noplaylist': True,
        'quiet': False,
        'verbose': False,
        'allow_unsecure_tools': True,
        'remote_components': ['ejs:github', 'ejs:npm'],
        'extractor_args': {
            'youtube': {
                'remote_components': ['ejs:github', 'ejs:npm']
            }
        },
        'sleep_interval_requests': 2,
        'socket_timeout': 30,
        'ignoreerrors': False,
        'nocheckcertificate': True,
        'prefer_insecure': True,
        'allow_unsecure_tools': True,
    }

    # Proxy logic
    if os.environ.get('FLASK_ENV') == 'production':
        if is_proxy_reachable(PROXY_URL):
            app.logger.info(f"Using proxy: {PROXY_URL}")
            ydl_opts['proxy'] = PROXY_URL
        else:
            app.logger.warning("Proxy is unreachable. Falling back to direct connection.")
    else:
        app.logger.info("Running in development mode, no proxy used.")

    # Fetch PO Token if on cloud (helps bypass "Sign in to confirm you're not a bot")
    po_token, visitor_data = get_po_token()
    if po_token and visitor_data:
        app.logger.info("Using PO Token for download")
        ydl_opts['extractor_args']['youtube']['po_token'] = [f"web+{po_token}"]
        # Note: some newer versions of yt-dlp might need different formatting for extractor-args

    # Use cookies if available (required for cloud servers blocked by YouTube)
    if os.path.exists(COOKIES_FILE):
        ydl_opts['cookiefile'] = COOKIES_FILE

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            raw_filename = ydl.prepare_filename(info)
            base, _ = os.path.splitext(raw_filename)
            mp3_filename = base + '.mp3'

        if not os.path.exists(mp3_filename):
            return jsonify({'error': 'Failed to generate MP3 file'}), 500

        # Read the file fully into memory first, then delete it
        # This prevents race condition where file is deleted before browser finishes downloading
        import io
        with open(mp3_filename, 'rb') as f:
            file_data = io.BytesIO(f.read())
        os.remove(mp3_filename)

        file_data.seek(0)
        return send_file(
            file_data,
            as_attachment=True,
            download_name=os.path.basename(mp3_filename),
            mimetype='audio/mpeg'
        )

    except Exception as e:
        error_msg = str(e)
        app.logger.error(f"Download error: {error_msg}")
        
        # User-friendly error for bot detection
        if "Sign in to confirm you're not a bot" in error_msg or "confirm you're not a bot" in error_msg:
            return jsonify({
                'error': 'YouTube detected a bot challenge. Please upload fresh cookies via the Authentication tab.',
                'code': 'BOT_DETECTION'
            }), 403
        
        if "Requested format is not available" in error_msg:
            return jsonify({
                'error': 'Requested format not available. This usually means YouTube is blocking the server. Try refreshing cookies.',
                'code': 'FORMAT_UNAVAILABLE'
            }), 400

        return jsonify({'error': error_msg}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
