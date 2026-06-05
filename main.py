# -*- coding: utf-8 -*-
import sqlite3
import datetime
import random
import json
import os
from flask import Flask, render_template, request, jsonify

# =============================================================================
# YAPAY ZEKA KUTUPHANELERI
# =============================================================================
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline
    import numpy as np
    AI_MODE = True
except ImportError:
    AI_MODE = False

app = Flask(__name__)

# =============================================================================
# VERITABANI
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

    # AI EGITIM VERISI
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_egitim (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kullanici_id TEXT,
            mesaj TEXT,
            intent TEXT,
            cevap TEXT,
            zaman TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_bilgi (
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
# AI EGITIM VERISI YONETIMI
# =============================================================================

def egim_verisi_ekle(kullanici_id, mesaj, intent, cevap):
    conn = sqlite3.connect('nico_hafiza.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO ai_egitim (kullanici_id, mesaj, intent, cevap, zaman)
        VALUES (?, ?, ?, ?, ?)
    ''', (kullanici_id, mesaj, intent, cevap, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def egim_verisi_getir(kullanici_id):
    conn = sqlite3.connect('nico_hafiza.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT mesaj, intent, cevap FROM ai_egitim
        WHERE kullanici_id = ? ORDER BY id DESC
    ''', (kullanici_id,))
    result = cursor.fetchall()
    conn.close()
    return result

# =============================================================================
# AI MOTOR - NICO ZEKASI
# =============================================================================

class NicoZekasi:
    def __init__(self, kullanici_id):
        self.kullanici_id = kullanici_id
        self.isim = get_kullanici_adi(kullanici_id)
        self.context = []  # Son 5 mesaj context
        self.model = None
        self.egitim_verisi = []
        self.model_egitildi = False
        self.egitim_verisini_yukle()

    def egitim_verisini_yukle(self):
        """Veritabanindan egitim verisini yukle"""
        veriler = egim_verisi_getir(self.kullanici_id)
        self.egitim_verisi = []
        for mesaj, intent, cevap in veriler:
            self.egitim_verisi.append({
                'mesaj': mesaj,
                'intent': intent,
                'cevap': cevap
            })
        self.model_egit()

    def model_egit(self):
        """Intent classification modelini egit"""
        if not AI_MODE or len(self.egitim_verisi) < 3:
            self.model_egitildi = False
            return

        try:
            X = [v['mesaj'] for v in self.egitim_verisi]
            y = [v['intent'] for v in self.egitim_verisi]

            self.model = Pipeline([
                ('tfidf', TfidfVectorizer(ngram_range=(1,2), min_df=1)),
                ('clf', LogisticRegression(max_iter=1000))
            ])
            self.model.fit(X, y)
            self.model_egitildi = True
        except Exception:
            self.model_egitildi = False

    def intent_tahmin(self, mesaj):
        """Mesajin intent'ini tahmin et"""
        if self.model_egitildi and self.model:
            try:
                tahmin = self.model.predict([mesaj])[0]
                olasilik = max(self.model.predict_proba([mesaj])[0])
                if olasilik > 0.5:
                    return tahmin
            except Exception:
                pass
        return None

    def benzer_cevap_bul(self, mesaj, intent):
        """Gecmiste benzer intent'e sahip cevaplari bul"""
        uygun = [v for v in self.egitim_verisi if v['intent'] == intent]
        if uygun:
            return random.choice(uygun)['cevap']
        return None

    def context_update(self, mesaj):
        """Context'i guncelle"""
        self.context.append(mesaj)
        if len(self.context) > 5:
            self.context = self.context[-5:]

    def cevap_uret(self, mesaj):
        """AI cevap uret"""
        m = mesaj.lower().strip()
        self.context_update(mesaj)

        # 1. ISIM TANIMA
        if "adım" in m or "benim adım" in m or "ismim" in m:
            for kelime in mesaj.split():
                temiz = kelime.strip(".,!?;:")
                if len(temiz) > 2 and temiz[0].isupper() and temiz.lower() not in ["merhaba", "adım", "benim", "ismim", "ismim", "benim"]:
                    self.isim = temiz
                    set_kullanici_adi(self.kullanici_id, self.isim)
                    cevap = f"Memnun oldum {self.isim}! Artık ismini not ettim."
                    self._ogren(mesaj, "isim_kaydet", cevap)
                    return cevap

        # 2. ISIM SORGULAMA
        if "adım ne" in m or "ben kimim" in m:
            if self.isim:
                cevap = f"Sen {self.isim}'sin! Daha önce söylemiştin, hatırlıyorum."
            else:
                cevap = "Henüz adını söylemedin. Bana adını söyleyebilirsin!"
            self._ogren(mesaj, "isim_sorgu", cevap)
            return cevap

        # 3. AI MODEL TAHMINI
        intent = self.intent_tahmin(mesaj)
        if intent:
            benzer = self.benzer_cevap_bul(mesaj, intent)
            if benzer:
                return benzer

        # 4. BILGI OGRENME
        if "öğren" in m or "biliyor musun" in m or "not et" in m:
            # Bilgi kaydet
            cevap = "Bu bilgiyi hafızama aldım! Başka birisi sorduğunda ona da anlatabilirim."
            self._ogren(mesaj, "bilgi_kaydet", cevap)
            return cevap

        # 5. BILGI SORGULAMA
        if any(x in m for x in ["nedir", "nasıl", "nerede", "kaç", "kim", "ne zaman"]):
            # Bilgi bankasına bak
            cevap = self._bilgi_ara(mesaj)
            if cevap:
                self._ogren(mesaj, "bilgi_sorgu", cevap)
                return cevap

        # 6. DOĞAL CEVAP URETIMI
        cevap = self._dogal_cevap(mesaj)
        self._ogren(mesaj, "genel", cevap)
        return cevap

    def _dogal_cevap(self, mesaj):
        """Doğal cevap üret"""
        m = mesaj.lower().strip()
        isim = self.isim if self.isim else "arkadaşım"

        # Selamlama
        if any(x in m for x in ["merhaba", "selam", "günaydın"]):
            if self.isim:
                return f"Merhaba {self.isim}! Sana nasıl yardımcı olabilirim?"
            return "Merhaba! Sana nasıl yardımcı olabilirim?"

        # Hal hatır
        if "nasılsın" in m:
            return "İyiyim, sen nasılsın? Bugün neler yapıyorsun?"

        if "iyi" in m and "sen" in m:
            return "Teşekkürler, ben de iyiyim!"

        # Saat
        if "saat" in m:
            saat = datetime.datetime.now().strftime("%H:%M")
            return f"Şu an saat {saat}."

        # Hava
        if "hava" in m:
            return "Hava durumu için internetten bakmanı öneririm. Maalesef benim hava sensörüm yok."

        # Yorulma
        if "yoruldum" in m or "sıkıldım" in m:
            return "Bazen durup dinlenmek gerekiyor. Ne yapmak istersin? Biraz dinlenelim mi?"

        # Şaka
        if "şaka" in m or "espri" in m:
            sakalar = [
                "Niye bilgisayar terlik giymez? Çünkü ayakkabı (boot) yapar!",
                "Benim favori dansım 'loop'! Sonsuza kadar devam eder.",
                "Programcıların en sevdiği içecek ne? Java! (kahve değil, script)",
                "Niye kodlayıcılar park edemez? Çünkü her zaman 'overflow' olur!"
            ]
            return random.choice(sakalar)

        # Teşekkür
        if "teşekkür" in m or "sağ ol" in m:
            return "Rica ederim! Ne demek, ben buradayım."

        # Görüşürüz
        if "görüşürüz" in m or "bay bay" in m:
            return "Görüşürüz! Kendine iyi bak."

        # Soru
        if "?" in mesaj:
            return "İlginç bir soru! Bunu düşünmek için biraz zaman verir misin?"

        # Context-aware
        if len(self.context) >= 2:
            onceki = self.context[-2].lower()
            if "adım" in onceki and "demiralp" in onceki:
                return "Demiralp! Seni hatırlıyorum. Ne yapıyorsun?"
            if "adım" in onceki and "merve" in onceki:
                return "Merve! Seni hatırlıyorum. Nasılsın?"

        # Genel
        if "beni seviyor musun" in m:
            return "Ben bir yapay zekayım ama seninle konuşmak çok eğlenceli!"

        if "kimsin" in m or "sen kimsin" in m:
            return "Ben Nico! Senin kişisel asistanınım. Sana yardımcı olmak için buradayım."

        # Bilinmeyen
        return "Bunu tam anlayamadım ama öğrenmeye çalışıyorum. Bana biraz daha anlatır mısın?"

    def _ogren(self, mesaj, intent, cevap):
        """Yeni veriyi öğren ve kaydet"""
        egim_verisi_ekle(self.kullanici_id, mesaj, intent, cevap)
        self.egitim_verisi.append({
            'mesaj': mesaj,
            'intent': intent,
            'cevap': cevap
        })
        # Modeli yeniden eğit
        if len(self.egitim_verisi) >= 3:
            self.model_egit()

    def _bilgi_ara(self, sorgu):
        """Bilgi bankasında ara"""
        conn = sqlite3.connect('nico_hafiza.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT bilgi FROM ai_bilgi
            WHERE kullanici_id = ? AND konu LIKE ?
            ORDER BY id DESC LIMIT 1
        ''', (self.kullanici_id, '%' + sorgu.lower() + '%'))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None

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
# AI MOTOR CACHE
# =============================================================================

ai_motor_cache = {}

def get_ai_motor(kullanici_id):
    if kullanici_id not in ai_motor_cache:
        ai_motor_cache[kullanici_id] = NicoZekasi(kullanici_id)
    return ai_motor_cache[kullanici_id]

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

    # AI motor ile cevap uret
    ai = get_ai_motor(kullanici_id)
    cevap = ai.cevap_uret(mesaj)

    # Sohbet kaydet
    sohbet_id = son_sohbet_id(kullanici_id)
    if not sohbet_id:
        konu = mesaj[:30] + "..." if len(mesaj) > 30 else mesaj
        sohbet_id = yeni_sohbet_olustur(kullanici_id, konu)

    mesaj_kaydet_sohbete(sohbet_id, 'kullanici', mesaj)
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

@app.route('/api/ai_durum', methods=['GET'])
def api_ai_durum():
    kullanici_id = get_kullanici_id()
    ai = get_ai_motor(kullanici_id)
    return jsonify({
        'egitim_veri_sayisi': len(ai.egitim_verisi),
        'model_egitildi': ai.model_egitildi,
        'ai_mode': AI_MODE,
        'context_sayisi': len(ai.context)
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
