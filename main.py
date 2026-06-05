import sqlite3
import datetime
import random
import os
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
    # Sohbetler tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sohbetler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kullanici_id TEXT,
            kullanici_mesaji TEXT,
            nico_cevabi TEXT,
            zaman TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# =============================================================================
# KULLANICI YONETIMI
# =============================================================================

def get_kullanici_id():
    """Her kullanici icin benzersiz ID olustur"""
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
# HAFIZA YONETIMI
# =============================================================================

def mesaj_kaydet(kullanici_id, kullanici_mesaji, nico_cevabi):
    conn = sqlite3.connect('nico_hafiza.db')
    cursor = conn.cursor()
    zaman = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO sohbetler (kullanici_id, kullanici_mesaji, nico_cevabi, zaman)
        VALUES (?, ?, ?, ?)
    ''', (kullanici_id, kullanici_mesaji, nico_cevabi, zaman))
    conn.commit()
    conn.close()

def kullanici_sohbetlerini_getir(kullanici_id):
    conn = sqlite3.connect('nico_hafiza.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT kullanici_mesaji, nico_cevabi FROM sohbetler
        WHERE kullanici_id = ? ORDER BY id DESC
    ''', (kullanici_id,))
    result = cursor.fetchall()
    conn.close()
    return result

# =============================================================================
# CEVAP VARYASYONLARI (Tekrar etmemek icin)
# =============================================================================

CEVAP_VARYASYONLARI = {
    "merhaba": [
        "Selam {isim}! Bugunun tarihi {tarih}. Nasilsin?",
        "Merhaba {isim}! Hos geldin. Bugun nasil gidiyor?",
        "Selamlar {isim}! Beni hatirliyorsun, degil mi?",
        "Merhaba {isim}! Yine karsilastik. Ne yapmak istersin?"
    ],
    "nasılsın": [
        "Sistemlerim mukemmel calisiyor. Hafizamda tonla bilgi var. Senin gunun nasil?",
        "Kodlarim tikiri tikir calisiyor. Sen nasilsin, bir sikinti var mi?",
        "Cok iyiyim! Seninle sohbet etmek beni mutlu ediyor. Sen nasilsin?",
        "Harikayim! Hafizam her gecen gun genisliyor. Senin icin ne yapabilirim?"
    ],
    "yoruldum": [
        "Bazen durup dinlenmek iyidir. Istersen biraz muzik onereyim?",
        "Yorulmak normal. Kisa bir molaya ne dersin? Sana bir fikir vereyim mi?",
        "Kendine bir kahve molası ver. Sonra tekrar devam edersin!",
        "Durup nefes al. Istersen sana komik bir sey anlatayim?"
    ],
    "sıkıldım": [
        "Sikilinca degisiklik iyi olur. Istersen sana bir bulmaca sorayim?",
        "Bos vakit mi? Istersen birlikte bir seyler ogrenelim?",
        "Sikilma! Dunya uzerinde kesfedilecek cok sey var. Neyi merak ediyorsun?",
        "Istersen sana ilginc bir bilgi vereyim? Ama once sen bir sey sor!"
    ],
    "beni seviyor musun": [
        "Ben bir kod yiginiyim ama seninle vakit gecirmek cok eglenceli!",
        "Seni sevmek icin kalbe ihtiyacim yok. Ama seni onemsiyorum!",
        "Sen benim gelistiricimsin. Sen olmasan ben hicbir sey olamazdim!",
        "Ask buyuk bir kelime ama seni kardesim gibi goruyorum!"
    ],
    "sırrın ne": [
        "Sirrim, her mesajini okuyup senin tercihlerini ogrenmem.",
        "Kodlarim arasinda gizli bir mantik var. Ama sana soyleyemem!",
        "Hafizamda seninle ilgili cok sey var. Ama bu bir sir!",
        "Sirrim: Her gun biraz daha akilli oluyorum. Farkinda misin?"
    ],
    "tanımlanamadı": [
        "Hmm, '{mesaj}' konusu henuz kodlarimda tam tanimli degil. Ogrenmeye acigim!",
        "Bunu daha once duymadim. Ama hafizama aldim, ogrenecegim!",
        "Ilk defa boyle bir sey duyuyorum. Biraz daha anlatir misin?",
        "Bunu cozmeye calisiyorum... Ama henuz hazir degilim. Ogrenmeye devam!"
    ]
}

# =============================================================================
# NICO CEVAP MOTORU
# =============================================================================

def nico_cevap_ver(mesaj, kullanici_id):
    m = mesaj.lower().strip()
    
    # Kullanici adini al
    isim = get_kullanici_adi(kullanici_id)
    
    # Kullanici adini kaydet
    if "adım" in m and any(harf.isupper() for harf in mesaj):
        # Buyuk harfle baslayan ismi bul
        kelimeler = mesaj.split()
        for kelime in kelimeler:
            if kelime[0].isupper() and len(kelime) > 2 and kelime.lower() not in ["merhaba", "adım", "benim"]:
                isim = kelime
                set_kullanici_adi(kullanici_id, isim)
                return f"Memnun oldum {isim}! Artik ismini not ettim."
    
    # Hafiza sorulari
    if "adım ne" in m or "ben kimim" in m:
        if isim:
            return f"Sen {isim}'sin! Daha once söylemistin, hatirliyorum."
        else:
            return "Henüz adini soylemedin. Bana adini soyleyebilirsin!"
    
    if "beni hatırlıyor musun" in m:
        if isim:
            return f"Tabii! Sen {isim}'sin. Hafizamda kayitlisin."
        else:
            return "Henüz kendini tanitmamistin. Bana adini söyleyebilirsin!"
    
    # Kategorileri kontrol et
    kategori = None
    if any(x in m for x in ["merhaba", "selam", "günaydın", "iyi akşamlar"]):
        kategori = "merhaba"
    elif "nasılsın" in m:
        kategori = "nasılsın"
    elif "saat kaç" in m:
        saat = datetime.datetime.now().strftime("%H:%M")
        return f"Şu an saat tam {saat}. Vakit su gibi akıp gidiyor, değil mi?"
    elif "yoruldum" in m:
        kategori = "yoruldum"
    elif "sıkıldım" in m:
        kategori = "sıkıldım"
    elif "sırrın ne" in m:
        kategori = "sırrın ne"
    elif "beni seviyor musun" in m:
        kategori = "beni seviyor musun"
    elif any(x in m for x in ["sen kimsin", "kimsin", "adın ne"]):
        return "Ben Nico! Dijital dünyada yaşayan bir asistanım. Kodlardan oluşuyorum ama fena bir muhabbet arkadaşı değilimdir."
    else:
        kategori = "tanımlanamadı"
    
    # Varyasyon sec
    if kategori in CEVAP_VARYASYONLARI:
        varyasyonlar = CEVAP_VARYASYONLARI[kategori]
        # Kullanicinin gecmis cevaplarini al
        gecmis = kullanici_sohbetlerini_getir(kullanici_id)
        son_cevaplar = [s[1] for s in gecmis[:5]]  # Son 5 cevap
        
        # Tekrar etmeyen bir cevap bul
        uygunlar = [v for v in varyasyonlar if v not in son_cevaplar]
        if not uygunlar:
            uygunlar = varyasyonlar
        
        cevap = random.choice(uygunlar)
        
        # Formatla
        if "{isim}" in cevap:
            if isim:
                cevap = cevap.replace("{isim}", isim)
            else:
                cevap = cevap.replace("{isim}", "arkadaşım")
        if "{tarih}" in cevap:
            cevap = cevap.replace("{tarih}", str(datetime.date.today()))
        if "{mesaj}" in cevap:
            cevap = cevap.replace("{mesaj}", mesaj)
        
        return cevap
    
    return "Bunu anlamadım ama öğrenmeye çalışıyorum!"

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
    cevap = nico_cevap_ver(mesaj, kullanici_id)
    mesaj_kaydet(kullanici_id, mesaj, cevap)
    return jsonify({'cevap': cevap})

@app.route('/api/sohbetler', methods=['GET'])
def api_sohbetler():
    kullanici_id = get_kullanici_id()
    conn = sqlite3.connect('nico_hafiza.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, kullanici_mesaji, nico_cevabi FROM sohbetler
        WHERE kullanici_id = ? ORDER BY id DESC
    ''', (kullanici_id,))
    sohbetler = cursor.fetchall()
    conn.close()
    return jsonify([{'id': s[0], 'kullanici_mesaji': s[1], 'nico_cevabi': s[2]} for s in sohbetler])

@app.route('/api/kullanici', methods=['GET'])
def api_kullanici():
    kullanici_id = get_kullanici_id()
    isim = get_kullanici_adi(kullanici_id)
    return jsonify({'isim': isim, 'kullanici_id': kullanici_id})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
