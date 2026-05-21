"""Start the Flask dev server on a free port and verify a real HTTP download."""
import os
import shutil
import socket
import subprocess
import sys
import time

import requests

BASE_DIR = r'D:\.gemini\antigravity\scratch\ytdownloader'
os.chdir(BASE_DIR)


def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


port = find_free_port()
shutil.rmtree('downloads', ignore_errors=True)
os.makedirs('downloads', exist_ok=True)

env = {**os.environ, 'PYTHONUNBUFFERED': '1', 'PORT': str(port)}
log_path = os.path.join(BASE_DIR, f'test_server_{port}.log')

with open(log_path, 'w', encoding='utf-8') as log_file:
    proc = subprocess.Popen(
        [sys.executable, '-u', 'app.py'],
        stdout=log_file,
        stderr=subprocess.STDOUT,
        text=True,
        env=env
    )

    time.sleep(4)

    try:
        response = requests.post(
            f'http://127.0.0.1:{port}/api/download',
            json={'url': 'https://www.youtube.com/watch?v=jNQXAC9IVRw', 'format': 'mp3'},
            timeout=180
        )
        print(f'Port: {port}')
        print(f'Status: {response.status_code}')
        if response.status_code != 200:
            print(f'Response: {response.text[:500]}')
        else:
            print(f'Content-Type: {response.headers.get("Content-Type")}')
            print(f'Content-Length: {len(response.content)}')
    except Exception as error:
        print(f'Port: {port}')
        print(f'Error: {type(error).__name__}: {error}')
    finally:
        proc.terminate()
        proc.wait(timeout=10)

print(f'Log file: {log_path}')
