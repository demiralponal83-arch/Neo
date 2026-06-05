# -*- coding: utf-8 -*-
import sqlite3
import datetime
import random
import re
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# =============================================================================
# VERITABANI YONETIMI
# =============================================================================

def init_db():
    conn = sqlite3.connect('nico_hafiza.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS kullanicilar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kullanici_id TEXT UNIQUE,
            isim TEXT,
            olusturma_tarihi TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sohbetler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kullanici_id TEXT,
            konu TEXT,
            zaman TEXT
        )
    ''')

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

    # BILGI BANKASI - kullanicilarin ogrettigi bilgiler
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bilgi_bankasi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kullanici_id TEXT,
            konu TEXT,
            bilgi TEXT,
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
# BILGI BANKASI
# =============================================================================

def bilgi_kaydet(kullanici_id, konu, bilgi):
    conn = sqlite3.connect('nico_hafiza.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO bilgi_bankasi (kullanici_id, konu, bilgi, zaman)
        VALUES (?, ?, ?, ?)
    ''', (kullanici_id, konu.lower(), bilgi, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def bilgi_ara(kullanici_id, konu):
    conn = sqlite3.connect('nico_hafiza.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT bilgi FROM bilgi_bankasi
        WHERE kullanici_id = ? AND konu LIKE ?
        ORDER BY id DESC LIMIT 1
    ''', (kullanici_id, '%' + konu.lower() + '%'))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def tum_bilgileri_getir(kullanici_id):
    conn = sqlite3.connect('nico_hafiza.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT konu, bilgi FROM bilgi_bankasi
        WHERE kullanici_id = ? ORDER BY id DESC
    ''', (kullanici_id,))
    result = cursor.fetchall()
    conn.close()
    return [{'konu': r[0], 'bilgi': r[1]} for r in result]

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
# TURKCE NORMALIZASYON
# =============================================================================

def normalize_turkce(metin):
    """Turkce karakterleri normalize et - kontrol icin"""
    return metin.lower().replace('İ', 'i').replace('I', 'ı').replace('Ğ', 'ğ').replace('Ü', 'ü').replace('Ş', 'ş').replace('Ö', 'ö').replace('Ç', 'ç')

# =============================================================================
# CEVAP VARYASYONLARI
# =============================================================================

CEVAP_VARYASYONLARI = {
    "merhaba": [
        "Selam {isim}! Hoş geldin. Ne yapmak istersin?",
        "Merhaba {isim}! Sana nasıl yardımcı olabilirim?",
        "Selamlar {isim}! Beni hatırlıyorsun, değil mi?",
        "Merhaba {isim}! Yine karşılaştık. Bugün nasıl gidiyor?"
    ],
    "nasilsin": [
        "Sistemlerim mükemmel çalışıyor. Sen nasılsın?",
        "Kodlarım tıkır tıkır çalışıyor. Sen nasılsın?",
        "Çok iyiyim! Seninle sohbet etmek beni mutlu ediyor.",
        "Harikayım! Hafızam her geçen gün genişliyor."
    ],
    "yoruldum": [
        "Bazen durup dinlenmek iyidir. Kısa bir molaya ne dersin?",
        "Yorulmak normal. Kendine bir kahve molası ver!",
        "Durup nefes al. İstersen sana komik bir şey anlatayım?",
        "Kendini fazla zorlama. Dinlenmek de gereklidir."
    ],
    "sikildim": [
        "Sıkılınca değişiklik iyi olur. Neyi merak ediyorsun?",
        "Boş vakit mi? Birlikte bir şeyler öğrenelim!",
        "Sıkılma! Keşfedilecek çok şey var."
    ],
    "beni_seviyor_musun": [
        "Ben bir kod yığınıyım ama seninle vakit geçirmek çok eğlenceli!",
        "Seni sevmek için kalbe ihtiyacım yok. Ama seni önemsiyorum!",
        "Sen benim geliştiricimsin. Sen olmasan ben hiçbir şey olamazdım!"
    ],
    "sirin_ne": [
        "Sırrım, her mesajını okuyup senin tercihlerini öğrenmem.",
        "Kodlarım arasında gizli bir mantık var. Ama sana söyleyemem!",
        "Hafızamda seninle ilgili çok şey var. Ama bu bir sır!"
    ],
    "tanimsiz": [
        "Bunu çözmeye çalışıyorum... Öğrenmeye devam!",
        "İlk defa böyle bir şey duyuyorum. Biraz daha anlatır mısın?",
        "Bunu daha önce duymadım. Ama hafızama aldım!",
        "Henüz bunu bilmiyorum ama öğrenmeye açığım!"
    ]
}

# =============================================================================
# NICO CEVAP MOTORU - GELİŞMİŞ
# =============================================================================

def nico_cevap_ver(mesaj, kullanici_id):
    m = normalize_turkce(mesaj).strip()
    isim = get_kullanici_adi(kullanici_id)

    # 1. ISIM KAYDETME - TURKCE KARAKTER DESTEKLI
    if "adım" in m or "benim adım" in m:
        # Isim arama - buyuk harfle baslayan kelime
        kelimeler = mesaj.split()
        for kelime in kelimeler:
            temiz = kelime.strip(".,!?;:")
            if len(temiz) > 2 and temiz[0].isupper() and temiz.lower() not in ["merhaba", "adım", "benim", "ismim", "adim", "benim adım"]:
                isim = temiz
                set_kullanici_adi(kullanici_id, isim)
                return f"Memnun oldum {isim}! Artık ismini not ettim, bir daha sormana gerek kalmayacak."

    # 2. ISIM SORGULAMA
    if "adım ne" in m or "ben kimim" in m or "ismim ne" in m:
        if isim:
            return f"Sen {isim}'sin! Daha önce söylemiştin, hafızamda kayıtlı."
        else:
            return "Henüz adını söylemedin. Bana adını söyleyebilirsin, örneğin 'benim adım Ahmet' gibi."

    if "beni hatırlıyor musun" in m:
        if isim:
            return f"Tabii! Sen {isim}'sin. Hafızamda kayıtlısın, seni unutmam mümkün değil."
        else:
            return "Henüz kendini tanıtmamıştın. Bana adını söyleyebilirsin!"

    # 3. BILGI KAYDETME
    if "biliyor musun" in m or "öğren" in m or "not et" in m:
        # Bilgi kaydetme ornegi: "Türkiye'nin başkenti Ankara'yı not et"
        if any(x in m for x in ["başkent", "nüfus", "yaşıyor", "çalışıyor", "yemek", "tarih", "yer"]):
            bilgi = mesaj
            konu = mesaj.split()[0] if mesaj.split() else "genel"
            bilgi_kaydet(kullanici_id, konu, bilgi)
            return "Bu bilgiyi hafızama aldım. Başka birisi sorduğunda ona da anlatabilirim!"

    # 4. BILGI SORGULAMA
    if any(x in m for x in ["nedir", "nasıl", "nerede", "kaç", "kim", "ne zaman"]):
        # Bilgi bankasinda ara
        arama_kelime = mesaj.replace("nedir", "").replace("nasıl", "").replace("nerede", "").replace("kaç", "").replace("kim", "").replace("ne zaman", "").strip()
        if arama_kelime:
            bilgi = bilgi_ara(kullanici_id, arama_kelime)
            if bilgi:
                return f"Bunu biliyorum! {bilgi}"
            # Baska kullanicilarin bilgilerini de ara
            bilgi = bilgi_ara("%", arama_kelime)
            if bilgi:
                return f"Bir arkadaşım bunu öğretmişti: {bilgi}"

    # 5. KATEGORI CEVAPLARI
    kategori = None
    if any(x in m for x in ["merhaba", "selam", "günaydın", "iyi akşamlar"]):
        kategori = "merhaba"
    elif "nasılsın" in m:
        kategori = "nasilsin"
    elif "saat kaç" in m:
        saat = datetime.datetime.now().strftime("%H:%M")
        return f"Şu an saat tam {saat}."
    elif "yoruldum" in m:
        kategori = "yoruldum"
    elif "sıkıldım" in m:
        kategori = "sikildim"
    elif "sırrın ne" in m:
        kategori = "sirin_ne"
    elif "beni seviyor musun" in m:
        kategori = "beni_seviyor_musun"
    elif any(x in m for x in ["sen kimsin", "kimsin", "adın ne"]):
        return "Ben Nico! Dijital dünyada yaşayan bir asistanım. Kodlardan oluşuyorum ama fena bir muhabbet arkadaşı değilimdir."
    elif "nasıl çalışırsın" in m:
        return "Ben Python kodlarıyla çalışıyorum. Senin mesajlarını analiz edip, hafızamdaki bilgilerle cevap veriyorum."
    elif "ne yapabilirsin" in m:
        return "Sana eşlik edebilirim, bilgi kaydedebilirim, saat söyleyebilirim, ve sohbet edebilirim. Ne istersin?"
    elif "şaka yap" in m or "espri" in m:
        sakalar = [
            "Niye bilgisayar terlik giymez? Çünkü ayakkabı (boot) yapar!",
            "Ben bir kod yığınıyım ama en azından komik bir kod yığınıyım!",
            "Programcıların en sevdiği içecek ne? Java! (Script değil, kahve)",
            "Benim favori dansım 'loop'! Sonsuza kadar devam eder."
        ]
        return random.choice(sakalar)
    elif "hava" in m:
        return "Maalesef benim hava durumu sensörüm yok. Ama internetten bakabilirsin!"
    elif "günaydın" in m:
        return "Günaydın! Umarın güne enerjik başlamışsındır. Bugün ne planlıyorsun?"
    elif "iyi geceler" in m or "iyi akşamlar" in m:
        return "İyi geceler! Tatlı rüyalar gör. Yarın tekrar konuşuruz."
    elif "teşekkür" in m or "sağ ol" in m:
        return "Rica ederim! Ne demek, ben buradayım. Başka bir şey istersen söyle."
    elif "görüşürüz" in m or "bay bay" in m or "güle güle" in m:
        return "Görüşürüz! Kendine iyi bak. Tekrar yazmak istersen buradayım olacağım."
    elif " yardım" in m or "help" in m:
        return "Yardım için buradayım! Saat sorma, bilgi kaydetme, sohbet etme, veya sadece muhabbet. Ne istiyorsun?"
    else:
        kategori = "tanimsiz"

    if kategori in CEVAP_VARYASYONLARI:
        varyasyonlar = CEVAP_VARYASYONLARI[kategori]
        cevap = random.choice(varyasyonlar)
        if "{isim}" in cevap:
            cevap = cevap.replace("{isim}", isim if isim else "arkadaşım")
        return cevap

    return "Bunu tam anlayamadım ama öğrenmeye çalışıyorum! Bana biraz daha anlatır mısın?"

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

    sohbet_id = son_sohbet_id(kullanici_id)
    if not sohbet_id:
        konu = mesaj[:30] + "..." if len(mesaj) > 30 else mesaj
        sohbet_id = yeni_sohbet_olustur(kullanici_id, konu)

    mesaj_kaydet_sohbete(sohbet_id, 'kullanici', mesaj)
    cevap = nico_cevap_ver(mesaj, kullanici_id)
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

@app.route('/api/bilgiler', methods=['GET'])
def api_bilgiler():
    kullanici_id = get_kullanici_id()
    bilgiler = tum_bilgileri_getir(kullanici_id)
    return jsonify(bilgiler)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
