from flask import Flask, request, jsonify, render_template
import sqlite3
import json
import os
from datetime import datetime

app = Flask(__name__)
DB = 'pesagens.db'

def init_db():
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

def parse_campos(raw_campos_str):
    """Converte string de campos para lista, suportando JSON e formato antigo."""
    if not raw_campos_str:
        return []
    try:
        return json.loads(raw_campos_str)
    except Exception:
        # fallback para formato antigo
        return raw_campos_str.strip("[]").replace("'", "").split(', ')

@app.route('/')
def dashboard():
    conn = get_db()
    rows = conn.execute(
        'SELECT * FROM pesagens ORDER BY id DESC LIMIT 50'
    ).fetchall()
    conn.close()
    pesagens = []
    for row in rows:
        pesagens.append({
            'id':       row['id'],
            'recebido': row['recebido'],
            'campos':   parse_campos(row['campos']),
            'raw':      row['linha_raw']
        })
    return render_template('index.html', pesagens=pesagens)

@app.route('/debug')
def debug():
    """Página de diagnóstico — mostra os campos por posição (índice)."""
    conn = get_db()
    row = conn.execute(
        'SELECT * FROM pesagens ORDER BY id DESC LIMIT 1'
    ).fetchone()
    conn.close()
    if not row:
        return '<h2>Nenhum registro ainda.</h2>'

    campos = parse_campos(row['campos'])
    html = '<html><head><meta charset="UTF-8"><style>'
    html += 'body{font-family:monospace;padding:20px;background:#f5f5f5}'
    html += 'table{border-collapse:collapse;width:100%}'
    html += 'th{background:#1a3a5c;color:white;padding:8px 12px;text-align:left}'
    html += 'td{padding:8px 12px;border-bottom:1px solid #ddd;background:white}'
    html += 'tr:nth-child(even) td{background:#f9f9f9}'
    html += '</style></head><body>'
    html += f'<h2>Diagnóstico — Ticket #{row["id"]}</h2>'
    html += f'<p><b>Recebido:</b> {row["recebido"]}</p>'
    html += f'<p><b>Linha bruta:</b> <code style="word-break:break-all">{row["linha_raw"]}</code></p><br>'
    html += '<table><tr><th>Índice</th><th>Valor</th></tr>'
    for i, c in enumerate(campos):
        html += f'<tr><td>[{i}]</td><td>{c}</td></tr>'
    html += '</table></body></html>'
    return html

@app.route('/pesagem', methods=['POST'])
def receber_pesagem():
    dados = request.get_json(force=True)
    if not dados:
        return jsonify({'erro': 'dados invalidos'}), 400
    conn = get_db()
    conn.execute(
        'INSERT INTO pesagens (recebido, linha_raw, campos) VALUES (?, ?, ?)',
        (
            dados.get('horario_local') or datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
            dados.get('linha_raw', ''),
            json.dumps(dados.get('campos', []), ensure_ascii=False)
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

init_db()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
