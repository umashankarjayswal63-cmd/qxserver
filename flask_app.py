import os
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import sqlite3, secrets
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app, origins=['*'], supports_credentials=True)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE_DIR, 'licenses.db')

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS licenses (id INTEGER PRIMARY KEY AUTOINCREMENT, key TEXT UNIQUE, profile TEXT, expires TEXT, is_active INTEGER DEFAULT 1)')
    conn.commit()
    conn.close()

def make_key():
    return 'QX-' + secrets.token_hex(6).upper()

def valid_license(k):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('SELECT * FROM licenses WHERE key=? AND is_active=1', (k,))
    row = c.fetchone()
    conn.close()
    if not row: return None
    if datetime.now() > datetime.fromisoformat(row[3]): return None
    return {'key': row[1], 'profile': row[2]}

@app.route('/')
def home(): return 'Server is running!'

@app.route('/create-license')
def create_license():
    k = make_key()
    e = (datetime.now() + timedelta(days=30)).isoformat()
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('INSERT INTO licenses (key, profile, expires) VALUES (?, ?, ?)', (k, 'Guru', e))
    conn.commit()
    conn.close()
    return jsonify({'license': k, 'expires_in': '30 days'})

@app.route('/verify/', methods=['POST'])
def verify():
    data = request.get_json() or {}
    k = data.get('license', '').strip().upper()
    lic = valid_license(k)
    if lic: return jsonify({'success': True, 'profile': lic['profile']})
    return jsonify({'success': False, 'error': 'Invalid'})

@app.route('/script-endpoint/', methods=['POST', 'GET'])
def script_endpoint():
    p = os.path.join(BASE_DIR, 'quotex.js')
    if not os.path.exists(p):
        return 'console.error("quotex.js not found");', 200, {'Content-Type': 'application/javascript'}
    with open(p, 'r') as f:
        js = f.read()
    resp = make_response(js)
    resp.headers['Content-Type'] = 'application/javascript'
    return resp

init_db()
if __name__ == '__main__':
    app.run()
