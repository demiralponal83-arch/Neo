import os
from flask import Flask, render_template, request, jsonify
from database import init_db
import sqlite3

app = Flask(__name__)

# Veritabanını başlat
init_db()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/mesaj', methods=['POST'])
def mesaj_kaydet():
    data = request.get_json()
    kullanici_mesaji = data.get('kullanici_mesaji')
    nico_cevabi = data.get('nico_cevabi')
    
    conn = sqlite3.connect('nico_hafiza.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO sohbetler (kullanici_mesaji, nico_cevabi) VALUES (?, ?)', 
                   (kullanici_mesaji, nico_cevabi))
    conn.commit()
    conn.close()
    return jsonify({'durum': 'basarili'})

@app.route('/api/mesajlar', methods=['GET'])
def mesajlari_getir():
    conn = sqlite3.connect('nico_hafiza.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, kullanici_mesaji, nico_cevabi FROM sohbetler ORDER BY id DESC')
    mesajlar = cursor.fetchall()
    conn.close()
    return jsonify([{'id': m[0], 'kullanici_mesaji': m[1], 'nico_cevabi': m[2]} for m in mesajlar])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
