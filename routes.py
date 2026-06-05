# -*- coding: utf-8 -*-
import datetime
import random

from flask import render_template, request, jsonify, session, redirect, url_for
from flask_login import current_user
from app import app, db
from replit_auth import require_login, make_replit_blueprint
from models import User, Sohbetler, Mesajlar, AI_Egitim, AI_Bilgi

# Register Replit Auth blueprint
app.register_blueprint(make_replit_blueprint(), url_prefix="/auth")

# Make session permanent
@app.before_request
def make_session_permanent():
    session.permanent = True

# ============================================================
# KULLANICI YARDIMCILARI
# ============================================================
def get_kullanici_id():
    if current_user.is_authenticated:
        return current_user.id
    return None

def get_kullanici_adi(user_id):
    if not user_id:
        return None
    user = User.query.get(user_id)
    if user and user.first_name:
        return user.first_name
    return None

def set_kullanici_adi(user_id, isim):
    user = User.query.get(user_id)
    if user:
        user.first_name = isim
        db.session.commit()

# ============================================================
# AI EGITIM VERISI
# ============================================================
def egim_verisi_ekle(user_id, mesaj, intent, cevap):
    egitim = AI_Egitim(
        user_id=user_id,
        mesaj=mesaj,
        intent=intent,
        cevap=cevap,
        zaman=datetime.datetime.now()
    )
    db.session.add(egitim)
    db.session.commit()

def egim_verisi_getir(user_id):
    return AI_Egitim.query.filter_by(user_id=user_id).order_by(AI_Egitim.id.desc()).all()

# ============================================================
# AI MOTOR - NICO ZEKASI
# ============================================================
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline
    AI_MODE = True
except ImportError:
    AI_MODE = False

class NicoZekasi:
    def __init__(self, user_id):
        self.user_id = user_id
        self.isim = get_kullanici_adi(user_id)
        self.context = []
        self.model = None
        self.egitim_verisi = []
        self.model_egitildi = False
        self.egitim_verisini_yukle()

    def egitim_verisini_yukle(self):
        veriler = egim_verisi_getir(self.user_id)
        self.egitim_verisi = []
        for v in veriler:
            self.egitim_verisi.append({
                'mesaj': v.mesaj,
                'intent': v.intent,
                'cevap': v.cevap
            })
        self.model_egit()

    def model_egit(self):
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
        if self.model_egitildi and self.model:
            try:
                tahmin = self.model.predict([mesaj])[0]
                olasilik = max(self.model.predict_proba([mesaj])[0])
                if olasilik > 0.5:
                    return tahmin
            except Exception:
                pass
        return None

    def benzer_cevap_bul(self, intent):
        uygun = [v for v in self.egitim_verisi if v['intent'] == intent]
        if uygun:
            return random.choice(uygun)['cevap']
        return None

    def context_update(self, mesaj):
        self.context.append(mesaj)
        if len(self.context) > 5:
            self.context = self.context[-5:]

    def cevap_uret(self, mesaj):
        m = mesaj.lower().strip()
        self.context_update(mesaj)

        # ISIM TANIMA
        if "adım" in m or "benim adım" in m or "ismim" in m:
            for kelime in mesaj.split():
                temiz = kelime.strip(".,!?;:")
                if len(temiz) > 2 and temiz[0].isupper():
                    if temiz.lower() not in ["merhaba", "adım", "benim", "ismim"]:
                        self.isim = temiz
                        set_kullanici_adi(self.user_id, self.isim)
                        cevap = f"Memnun oldum {self.isim}! Artık ismini not ettim."
                        self._ogren(mesaj, "isim_kaydet", cevap)
                        return cevap

        # ISIM SORGULAMA
        if "adım ne" in m or "ben kimim" in m:
            if self.isim:
                cevap = f"Sen {self.isim}'sin! Daha önce söylemiştin, hatırlıyorum."
            else:
                cevap = "Henüz adını söylemedin. Bana adını söyleyebilirsin!"
            self._ogren(mesaj, "isim_sorgu", cevap)
            return cevap

        # AI MODEL TAHMINI
        intent = self.intent_tahmin(mesaj)
        if intent:
            benzer = self.benzer_cevap_bul(intent)
            if benzer:
                return benzer

        # BILGI OGRENME
        if "öğren" in m or "biliyor musun" in m or "not et" in m:
            cevap = "Bu bilgiyi hafızama aldım! Başka birisi sorduğunda ona da anlatabilirim."
            self._ogren(mesaj, "bilgi_kaydet", cevap)
            return cevap

        # BILGI SORGULAMA
        if any(x in m for x in ["nedir", "nasıl", "nerede", "kaç", "kim", "ne zaman"]):
            cevap = self._bilgi_ara(mesaj)
            if cevap:
                self._ogren(mesaj, "bilgi_sorgu", cevap)
                return cevap

        # DOGAL CEVAP
        cevap = self._dogal_cevap(mesaj)
        self._ogren(mesaj, "genel", cevap)
        return cevap

    def _dogal_cevap(self, mesaj):
        m = mesaj.lower().strip()
        if any(x in m for x in ["merhaba", "selam", "günaydın"]):
            if self.isim:
                return f"Merhaba {self.isim}! Sana nasıl yardımcı olabilirim?"
            return "Merhaba! Sana nasıl yardımcı olabilirim?"
        if "nasılsın" in m:
            return "İyiyim, sen nasılsın? Bugün neler yapıyorsun?"
        if "iyi" in m and "sen" in m:
            return "Teşekkürler, ben de iyiyim!"
        if "saat" in m:
            saat = datetime.datetime.now().strftime("%H:%M")
            return f"Şu an saat {saat}."
        if "hava" in m:
            return "Hava durumu için internetten bakmanı öneririm."
        if "yoruldum" in m or "sıkıldım" in m:
            return "Bazen durup dinlenmek gerekiyor. Ne yapmak istersin?"
        if "şaka" in m or "espri" in m:
            sakalar = [
                "Niye bilgisayar terlik giymez? Çünkü ayakkabı (boot) yapar!",
                "Benim favori dansım 'loop'! Sonsuza kadar devam eder."
            ]
            return random.choice(sakalar)
        if "teşekkür" in m or "sağ ol" in m:
            return "Rica ederim! Ne demek, ben buradayım."
        if "görüşürüz" in m or "bay bay" in m:
            return "Görüşürüz! Kendine iyi bak."
        if "?" in mesaj:
            return "İlginç bir soru! Bunu düşünmek için biraz zaman verir misin?"
        if "beni seviyor musun" in m:
            return "Ben bir yapay zekayım ama seninle konuşmak çok eğlenceli!"
        if "kimsin" in m or "sen kimsin" in m:
            return "Ben Nico! Senin kişisel asistanınım."
        return "BUNU_ANLAMADIM"

    def _ogren(self, mesaj, intent, cevap):
        if cevap == "BUNU_ANLAMADIM" or not cevap or len(cevap) < 5:
            return
        egim_verisi_ekle(self.user_id, mesaj, intent, cevap)
        self.egitim_verisi.append({
            'mesaj': mesaj,
            'intent': intent,
            'cevap': cevap
        })
        if len(self.egitim_verisi) >= 3:
            self.model_egit()

    def _bilgi_ara(self, sorgu):
        sonuc = AI_Bilgi.query.filter(
            AI_Bilgi.user_id == self.user_id,
            AI_Bilgi.konu.ilike(f'%{sorgu.lower()}%')
        ).order_by(AI_Bilgi.id.desc()).first()
        return sonuc.bilgi if sonuc else None

# ============================================================
# AI MOTOR CACHE
# ============================================================
ai_motor_cache = {}

def get_ai_motor(user_id):
    if user_id not in ai_motor_cache:
        ai_motor_cache[user_id] = NicoZekasi(user_id)
    return ai_motor_cache[user_id]

# ============================================================
# SOHBET YONETIMI
# ============================================================
def yeni_sohbet_olustur(user_id, konu):
    sohbet = Sohbetler(user_id=user_id, konu=konu, zaman=datetime.datetime.now())
    db.session.add(sohbet)
    db.session.commit()
    return sohbet.id

def mesaj_kaydet(sohbet_id, gonderen, mesaj):
    m = Mesajlar(sohbet_id=sohbet_id, gonderen=gonderen, mesaj=mesaj, zaman=datetime.datetime.now())
    db.session.add(m)
    db.session.commit()

def son_sohbet_id(user_id):
    sohbet = Sohbetler.query.filter_by(user_id=user_id).order_by(Sohbetler.id.desc()).first()
    return sohbet.id if sohbet else None

def sohbetleri_getir(user_id):
    sohbetler = Sohbetler.query.filter_by(user_id=user_id).order_by(Sohbetler.id.desc()).all()
    return [{'id': s.id, 'konu': s.konu, 'zaman': s.zaman.strftime("%Y-%m-%d %H:%M:%S")} for s in sohbetler]

def mesajlari_getir(sohbet_id):
    mesajlar = Mesajlar.query.filter_by(sohbet_id=sohbet_id).order_by(Mesajlar.id.asc()).all()
    return [{'gonderen': m.gonderen, 'mesaj': m.mesaj, 'zaman': m.zaman.strftime("%Y-%m-%d %H:%M:%S")} for m in mesajlar]

# ============================================================
# FLASK ROTALARI
# ============================================================

@app.route('/')
def home():
    if not current_user.is_authenticated:
        return render_template('login.html')
    return render_template('index.html')

@app.route('/api/cevap', methods=['POST'])
@require_login
def api_cevap():
    data = request.get_json()
    mesaj = data.get('mesaj', '')
    user_id = get_kullanici_id()

    ai = get_ai_motor(user_id)
    cevap = ai.cevap_uret(mesaj)

    if cevap == "BUNU_ANLAMADIM":
        if len(ai.context) >= 2:
            onceki = ai.context[-2].lower()
            if any(x in onceki for x in ["anlamad", "anlat", "demek istedi"]):
                cevap = f"Hmm, anladım sanmıştım ama galiba yanlış anladım. {get_kullanici_adi(user_id) or 'Dostum'}, bana farklı bir şekilde anlatır mısın?"
            else:
                cevap = f"Bunu anlamadım, kusura bakma. {get_kullanici_adi(user_id) or 'Dostum'}, bana biraz daha açık anlatır mısın?"
        else:
            cevap = "Bunu anlamadım, kusura bakma. Biraz daha açık anlatır mısın?"

    sohbet_id = son_sohbet_id(user_id)
    if not sohbet_id:
        konu = mesaj[:30] + "..." if len(mesaj) > 30 else mesaj
        sohbet_id = yeni_sohbet_olustur(user_id, konu)

    mesaj_kaydet(sohbet_id, 'kullanici', mesaj)
    mesaj_kaydet(sohbet_id, 'nico', cevap)

    return jsonify({'cevap': cevap})

@app.route('/api/sohbetler', methods=['GET'])
@require_login
def api_sohbetler():
    user_id = get_kullanici_id()
    return jsonify(sohbetleri_getir(user_id))

@app.route('/api/sohbet/<int:sohbet_id>', methods=['GET'])
@require_login
def api_sohbet_detay(sohbet_id):
    return jsonify(mesajlari_getir(sohbet_id))

@app.route('/api/yeni-sohbet', methods=['POST'])
@require_login
def api_yeni_sohbet():
    data = request.get_json()
    konu = data.get('konu', 'Yeni Sohbet')
    user_id = get_kullanici_id()
    sohbet_id = yeni_sohbet_olustur(user_id, konu)
    return jsonify({'sohbet_id': sohbet_id})

@app.route('/api/kullanici', methods=['GET'])
@require_login
def api_kullanici():
    user_id = get_kullanici_id()
    isim = get_kullanici_adi(user_id)
    return jsonify({'isim': isim, 'user_id': user_id})

@app.route('/api/ai_durum', methods=['GET'])
@require_login
def api_ai_durum():
    user_id = get_kullanici_id()
    ai = get_ai_motor(user_id)
    return jsonify({
        'egitim_veri_sayisi': len(ai.egitim_verisi),
        'model_egitildi': ai.model_egitildi,
        'ai_mode': AI_MODE,
        'context_sayisi': len(ai.context)
    })
