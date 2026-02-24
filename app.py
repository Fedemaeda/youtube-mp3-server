import os
import uuid
from flask import Flask, request, jsonify, render_template, send_file, after_this_request
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests from the Chrome Extension
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_FOLDER = os.path.join(BASE_DIR, 'downloads')
COOKIES_FILE = os.path.join(BASE_DIR, 'cookies.txt')

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
        'quiet': True,
        'source_address': '0.0.0.0',
        # Anti-bot detection measures
        'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
        'sleep_interval_requests': 1,
    }

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
        app.logger.error(f"Download error: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
