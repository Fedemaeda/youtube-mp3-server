import os
import uuid
from flask import Flask, request, jsonify, render_template, send_file, after_this_request
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests from the Chrome Extension
DOWNLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'downloads')

if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/download', methods=['POST'])
def download():
    data = request.get_json()
    url = data.get('url')

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

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            # yt-dlp's prepare_filename gives the original extension, we need to swap to .mp3 since postprocessor changes it
            raw_filename = ydl.prepare_filename(info)
            base, _ = os.path.splitext(raw_filename)
            mp3_filename = base + '.mp3'

        if not os.path.exists(mp3_filename):
            return jsonify({'error': 'Failed to generate MP3 file'}), 500

        @after_this_request
        def remove_file(response):
            try:
                os.remove(mp3_filename)
            except Exception as e:
                app.logger.error("Error removing or closing downloaded file handle", e)
            return response

        return send_file(mp3_filename, as_attachment=True, download_name=os.path.basename(mp3_filename))

    except Exception as e:
        app.logger.error(f"Download error: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Run the server on port 5000. Not suitable for production.
    app.run(host='0.0.0.0', port=5000, debug=True)
