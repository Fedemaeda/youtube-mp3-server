import os, sys, json, shutil

os.chdir(r'D:\.gemini\antigravity\scratch\ytdownloader')
os.environ['FLASK_ENV'] = 'development'

# Clear any previous caches
for d in ['__pycache__', 'downloads']:
    if os.path.exists(d):
        shutil.rmtree(d, ignore_errors=True)
os.makedirs('downloads', exist_ok=True)

sys.path.insert(0, '.')
# Force reimport
for mod in list(sys.modules.keys()):
    if 'app' in mod:
        del sys.modules[mod]

from app import app
with app.test_client() as c:
    r = c.post('/api/download', 
        data=json.dumps({'url': 'https://www.youtube.com/watch?v=jNQXAC9IVRw', 'format': 'mp3'}),
        content_type='application/json')
    print(f'Status: {r.status_code}')
    if r.status_code != 200:
        print(f'Response: {r.data.decode("utf-8", errors="replace")[:500]}')
    else:
        print(f'Content-Type: {r.content_type}')
        print(f'Content-Length: {len(r.data)}')
