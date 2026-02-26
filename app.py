from flask import Flask, request, jsonify, render_template
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
DB = 'pesagens.db'

def init_db():
    """Cria a tabela se não existir."""
    conn = sqlite3.connect(DB)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS pesagens (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            recebido   TEXT NOT NULL,
            linha_raw  TEXT,
            campos     TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def dashboard():
    conn = get_db()
    rows = conn.execute(
        'SELECT * FROM pesagens ORDER BY id DESC LIMIT 50'
    ).fetchall()
    conn.close()
    pesagens = []
    for row in rows:
        campos = row['campos'].strip("[]").replace("'", "").split(', ') if row['campos'] else []
        pesagens.append({
            'id':       row['id'],
            'recebido': row['recebido'],
            'campos':   campos,
            'raw':      row['linha_raw']
        })
    return render_template('index.html', pesagens=pesagens)

@app.route('/pesagem', methods=['POST'])
def receber_pesagem():
    dados = request.get_json()
    if not dados:
        return jsonify({'erro': 'dados invalidos'}), 400
    conn = get_db()
    conn.execute(
        'INSERT INTO pesagens (recebido, linha_raw, campos) VALUES (?, ?, ?)',
        (
            datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
            dados.get('linha_raw', ''),
            str(dados.get('campos', []))
        )
    )
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})

@app.route('/api/pesagens')
def api_pesagens():
    conn = get_db()
    rows = conn.execute(
        'SELECT * FROM pesagens ORDER BY id DESC LIMIT 50'
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

# Inicializa o banco ao carregar o módulo (funciona com gunicorn também)
init_db()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
