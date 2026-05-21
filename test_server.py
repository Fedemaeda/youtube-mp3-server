import os
os.environ['FLASK_ENV'] = 'development'
from app import app
app.run(host='127.0.0.1', port=5006, debug=True)
