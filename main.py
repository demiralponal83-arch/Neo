import sqlite3
import datetime
import random
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# =============================================================================
# VERITABANI YONETIMI
# =============================================================================

def init_db():
    conn = sqlite3.connect('nico_hafiza.db')
    cursor = conn.cursor()

    # Kullanicilar tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS kullanicilar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kullanici_id TEXT UNIQUE,
            isim TEXT,
            olusturma_tarihi TEXT
        )
    ''')

    # Sohbetler (konu basliklari) tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sohbetler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kullanici_id TEXT,
            konu TEXT,
            zaman TEXT
        )
    ''')

    # Mesajlar tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mesajlar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sohbet_id INTEGER,
            gonderen TEXT,
            mesaj TEXT,
            zaman TEXT,
            FOREIGN KEY (sohbet_id) REFERENCES sohbetler(id)
        )
    ''')

    conn.commit()
    conn.close()

init_db()

# =============================================================================
# KULLANICI YONETIMI
# =============================================================================

def get_kullanici_id():
    return request.headers.get('X-User-ID', 'default')

def get_kullanici_adi(kullanici_id):
    conn = sqlite3.connect('nico_hafiza.db')
    cursor = conn.cursor()
    cursor.execute('SELECT isim FROM kullanicilar WHERE kullanici_id = ?', (kullanici_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def set_kullanici_adi(kullanici_id, isim):
    conn = sqlite3.connect('nico_hafiza.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO kullanicilar (kullanici_id, isim, olusturma_tarihi)
        VALUES (?, ?, ?)
    ''', (kullanici_id, isim, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

# =============================================================================
# SOHBET YONETIMI
# =============================================================================

def yeni_sohbet_olustur(kullanici_id, konu):
    conn = sqlite3.connect('nico_hafiza.db')
    cursor = conn.cursor()
    zaman = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO sohbetler (kullanici_id, konu, zaman)
        VALUES (?, ?, ?)
    ''', (kullanici_id, konu, zaman))
    sohbet_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return sohbet_id

def mesaj_kaydet_sohbete(sohbet_id, gonderen, mesaj):
    conn = sqlite3.connect('nico_hafiza.db')
    cursor = conn.cursor()
    zaman = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO mesajlar (sohbet_id, gonderen, mesaj, zaman)
        VALUES (?, ?, ?, ?)
    ''', (sohbet_id, gonderen, mesaj, zaman))
    conn.commit()
    conn.close()

def son_sohbet_id(kullanici_id):
    """Son olusturulan sohbetin ID'sini dondur"""
    conn = sqlite3.connect('nico_hafiza.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id FROM sohbetler
        WHERE kullanici_id = ? ORDER BY id DESC LIMIT 1
    ''', (kullanici_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def sohbetleri_getir(kullanici_id):
    conn = sqlite3.connect('nico_hafiza.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, konu, zaman FROM sohbetler
        WHERE kullanici_id = ? ORDER BY id DESC
    ''', (kullanici_id,))
    result = cursor.fetchall()
    conn.close()
    return [{'id': r[0], 'konu': r[1], 'zaman': r[2]} for r in result]

def mesajlari_getir(sohbet_id):
    conn = sqlite3.connect('nico_hafiza.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT gonderen, mesaj, zaman FROM mesajlar
        WHERE sohbet_id = ? ORDER BY id ASC
    ''', (sohbet_id,))
    result = cursor.fetchall()
    conn.close()
    return [{'gonderen': r[0], 'mesaj': r[1], 'zaman': r[2]} for r in result]

# =============================================================================
# CEVAP VARYASYONLARI
# =============================================================================

CEVAP_VARYASYONLARI = {
    "merhaba": [
        "Selam {isim}! Hos geldin. Ne yapmak istersin?",
        "Merhaba {isim}! Sana nasil yardimci olabilirim?",
        "Selamlar {isim}! Beni hatirliyorsun, degil mi?",
        "Merhaba {isim}! Yine karsilastik."
    ],
    "nasilsin": [
        "Sistemlerim mukemmel calisiyor. Sen nasilsin?",
        "Kodlarim tikiri tikir calisiyor. Sen nasilsin?",
        "Cok iyiyim! Seninle sohbet etmek beni mutlu ediyor.",
        "Harikayim! Hafizam her gecen gun genisliyor."
    ],
    "yoruldum": [
        "Bazen durup dinlenmek iyidir. Kisa bir molaya ne dersin?",
        "Yorulmak normal. Kendine bir kahve molasi ver!",
        "Durup nefes al. Istersen sana komik bir sey anlatayim?",
        "Kendini fazla zorlama. Dinlenmek de gereklidir."
    ],
    "sikildim": [
        "Sikilinca degisiklik iyi olur. Neyi merak ediyorsun?",
        "Bos vakit mi? Birlikte bir seyler ogrenelim!",
        "Sikilma! Kesfedilecek cok sey var."
    ],
    "beni_seviyor_musun": [
        "Ben bir kod yiginiyim ama seninle vakit gecirmek cok eglenceli!",
        "Seni sevmek icin kalbe ihtiyacim yok. Ama seni onemsiyorum!",
        "Sen benim gelistiricimsin. Sen olmasan ben hicbir sey olamazdim!"
    ],
    "sirin_ne": [
        "Sirrim, her mesajini okuyup senin tercihlerini ogrenmem.",
        "Kodlarim arasinda gizli bir mantik var. Ama sana soyleyemem!",
        "Hafizamda seninle ilgili cok sey var. Ama bu bir sir!"
    ],
    "tanimsiz": [
        "Bunu cozmeye calisiyorum... Ogrenmeye devam!",
        "Ilk defa boyle bir sey duyuyorum. Biraz daha anlatir misin?",
        "Bunu daha once duymadim. Ama hafizama aldim!",
        "Henuz bunu bilmiyorum ama ogrenmeye acigim!"
    ]
}

# =============================================================================
# NICO CEVAP MOTORU
# =============================================================================

def nico_cevap_ver(mesaj, kullanici_id):
    m = mesaj.lower().strip()
    isim = get_kullanici_adi(kullanici_id)

    # Kullanici adini kaydet
    if "adim" in m and any(harf.isupper() for harf in mesaj):
        kelimeler = mesaj.split()
        for kelime in kelimeler:
            if kelime[0].isupper() and len(kelime) > 2 and kelime.lower() not in ["merhaba", "adim", "benim"]:
                isim = kelime
                set_kullanici_adi(kullanici_id, isim)
                return f"Memnun oldum {isim}! Artik ismini not ettim."

    # Hafiza sorulari
    if "adim ne" in m or "ben kimim" in m:
        if isim:
            return f"Sen {isim}'sin! Daha once soylemistin, hatirliyorum."
        else:
            return "Henuz adini soylemedin. Bana adini soyleyebilirsin!"

    if "beni hatirliyor musun" in m:
        if isim:
            return f"Tabii! Sen {isim}'sin. Hafizamda kayitlisin."
        else:
            return "Henuz kendini tanitmamistin. Bana adini soyleyebilirsin!"

    # Kategoriler
    kategori = None
    if any(x in m for x in ["merhaba", "selam", "gunaydin", "iyi aksamlar"]):
        kategori = "merhaba"
    elif "nasilsin" in m:
        kategori = "nasilsin"
    elif "saat kac" in m:
        saat = datetime.datetime.now().strftime("%H:%M")
        return f"Su an saat tam {saat}."
    elif "yoruldum" in m:
        kategori = "yoruldum"
    elif "sikildim" in m:
        kategori = "sikildim"
    elif "sirrin ne" in m:
        kategori = "sirin_ne"
    elif "beni seviyor musun" in m:
        kategori = "beni_seviyor_musun"
    elif any(x in m for x in ["sen kimsin", "kimsin", "adin ne"]):
        return "Ben Nico! Dijital dunyada yasayan bir asistanim."
    else:
        kategori = "tanimsiz"

    if kategori in CEVAP_VARYASYONLARI:
        varyasyonlar = CEVAP_VARYASYONLARI[kategori]
        cevap = random.choice(varyasyonlar)
        if "{isim}" in cevap:
            cevap = cevap.replace("{isim}", isim if isim else "arkadasim")
        return cevap

    return "Bunu anlamadim ama ogrenmeye calisiyorum!"

# =============================================================================
# FLASK ROTALARI
# =============================================================================

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/cevap', methods=['POST'])
def api_cevap():
    data = request.get_json()
    mesaj = data.get('mesaj', '')
    kullanici_id = get_kullanici_id()

    # Son sohbeti bul veya yeni olustur
    sohbet_id = son_sohbet_id(kullanici_id)

    # Eger sohbet yoksa, yeni olustur (konu = ilk mesaj)
    if not sohbet_id:
        konu = mesaj[:30] + "..." if len(mesaj) > 30 else mesaj
        sohbet_id = yeni_sohbet_olustur(kullanici_id, konu)

    # Kullanici mesajini kaydet
    mesaj_kaydet_sohbete(sohbet_id, 'kullanici', mesaj)

    # Nico cevap ver
    cevap = nico_cevap_ver(mesaj, kullanici_id)

    # Nico cevabini kaydet
    mesaj_kaydet_sohbete(sohbet_id, 'nico', cevap)

    return jsonify({'cevap': cevap})

@app.route('/api/sohbetler', methods=['GET'])
def api_sohbetler():
    kullanici_id = get_kullanici_id()
    sohbetler = sohbetleri_getir(kullanici_id)
    return jsonify(sohbetler)

@app.route('/api/sohbet/<int:sohbet_id>', methods=['GET'])
def api_sohbet_detay(sohbet_id):
    mesajlar = mesajlari_getir(sohbet_id)
    return jsonify(mesajlar)

@app.route('/api/yeni-sohbet', methods=['POST'])
def api_yeni_sohbet():
    data = request.get_json()
    konu = data.get('konu', 'Yeni Sohbet')
    kullanici_id = get_kullanici_id()
    sohbet_id = yeni_sohbet_olustur(kullanici_id, konu)
    return jsonify({'sohbet_id': sohbet_id})

@app.route('/api/kullanici', methods=['GET'])
def api_kullanici():
    kullanici_id = get_kullanici_id()
    isim = get_kullanici_adi(kullanici_id)
    return jsonify({'isim': isim, 'kullanici_id': kullanici_id})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
