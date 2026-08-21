# -*- coding: utf-8 -*-
import datetime
import json
import os
import random
import time
import urllib.error
import urllib.request
import re
import hashlib
import hmac
import secrets
import unicodedata
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import login_user, logout_user
from sqlalchemy import func

from flask import render_template, request, jsonify, session, redirect, url_for, send_from_directory
from flask_login import current_user
from app import app, db
from replit_auth import require_login, make_replit_blueprint
from models import (
    User,
    MobileToken,
    IPBlacklist,
    SecurityEvent,
    AccountAppeal,
    AppSetting,
    VisitorVisit,
    Sohbetler,
    Mesajlar,
    AI_Egitim,
    AI_Bilgi,
)

# Register Replit Auth blueprint
app.register_blueprint(make_replit_blueprint(), url_prefix="/auth")

# Make session permanent
@app.before_request
def make_session_permanent():
    session.permanent = True
    allowed_during_maintenance = {
        "maintenance", "admin_maintenance", "admin_dashboard",
        "admin_dashboard_unlock",
        "admin_maintenance", "admin_maintenance_update",
        "email_login", "email_register", "local_logout",
        "suspended_account",
        "appeal_account",
        "submit_account_appeal",
        "account_notice",
        "closed_account",
        "admin_test_login",
        "admin_test_exit",
        "admin_unsuspend_user",
        "admin_reopen_user",
        "mobile_login",
        "mobile_register",
        "mobile_logout",
        "mobile_current_user",
        "mobile_profile_update",
        "mobile_answer",
        "mobile_chats",
        "mobile_chat_detail",
        "mobile_chat_delete",
        "mobile_new_chat",
    }
    if request.path in {"/", "/giris", "/kayit"} and request.method in {"GET", "POST"}:
        visitor_key = session.get("_visitor_key")
        if not visitor_key:
            visitor_key = hashlib.sha256(os.urandom(32)).hexdigest()
            session["_visitor_key"] = visitor_key
        db.session.add(VisitorVisit(visitor_key=visitor_key, path=request.path))
        db.session.commit()
    if (
        maintenance_enabled()
        and request.endpoint not in allowed_during_maintenance
        and not request.path.startswith("/static/")
    ):
        return render_template("maintenance.html"), 503
    if (
        current_user.is_authenticated
        and getattr(current_user, "is_closed", False)
        and request.endpoint not in {
            "closed_account",
            "local_logout",
            "admin_unsuspend_user",
            "admin_reopen_user",
            "mobile_current_user",
            "mobile_profile_update",
            "mobile_answer",
            "mobile_chats",
            "mobile_chat_detail",
            "mobile_chat_delete",
            "mobile_new_chat",
        }
        and not request.path.startswith("/static/")
    ):
        response = app.make_response(render_template(
            "closed.html",
            user_name=current_user.first_name or current_user.email or "kullanıcı",
            profile_image_url=current_user.profile_image_url,
        ))
        response.status_code = 403
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        return response
    if (
        current_user.is_authenticated
        and getattr(current_user, "account_notice", None)
        and request.endpoint not in {"account_notice", "local_logout"}
        and not request.path.startswith("/static/")
    ):
        return redirect(url_for("account_notice"))
    if (
        current_user.is_authenticated
        and getattr(current_user, "is_suspended", False)
        and request.endpoint not in {
            "suspended_account",
            "appeal_account",
            "submit_account_appeal",
            "local_logout",
            "admin_unsuspend_user",
            "admin_reopen_user",
            "mobile_current_user",
            "mobile_profile_update",
            "mobile_answer",
            "mobile_chats",
            "mobile_chat_detail",
            "mobile_chat_delete",
            "mobile_new_chat",
        }
        and not request.path.startswith("/static/")
    ):
        response = app.make_response(render_template(
            "suspended.html",
            user_name=current_user.first_name or current_user.email or "kullanıcı",
            profile_image_url=current_user.profile_image_url,
        ))
        response.status_code = 403
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        return response

@app.route("/bakim")
def maintenance():
    return render_template("maintenance.html")

@app.route("/neo-sw.js")
def neo_service_worker():
    response = app.make_response(
        send_from_directory(app.static_folder, "neo-sw.js")
    )
    response.headers["Service-Worker-Allowed"] = "/"
    response.headers["Cache-Control"] = "no-cache"
    return response

def maintenance_enabled():
    setting = AppSetting.query.filter_by(key="maintenance_mode").first()
    if setting is not None:
        return setting.value == "true"
    return app.config.get("MAINTENANCE_MODE", False)

def mobile_user():
    authorization = request.headers.get("Authorization", "")
    if not authorization.startswith("Bearer "):
        return None
    raw_token = authorization[7:].strip()
    if not raw_token:
        return None
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    token = MobileToken.query.filter_by(token_hash=token_hash).first()
    return db.session.get(User, token.user_id) if token else None

def require_mobile_user():
    user = mobile_user()
    if user is None:
        return None, (jsonify({"error": "Mobil oturum geçersiz veya süresi dolmuş."}), 401)
    if user.is_closed:
        return None, (jsonify({"error": "Hesabınız kapatıldı.", "account_state": "closed"}), 403)
    if user.is_suspended:
        return None, (jsonify({"error": "Hesabınız askıya alındı.", "account_state": "suspended"}), 403)
    return user, None

def mobile_user_payload(user):
    return {
        "user_id": user.id,
        "isim": user.first_name,
        "soyisim": user.last_name,
        "email": user.email,
        "birth_date": user.birth_date.isoformat() if user.birth_date else None,
        "profile_image_url": user.profile_image_url,
        "profil_tamam": kullanici_profil_tamam(user),
        "account_state": "active",
    }

def mobile_token_response(user):
    raw_token = secrets.token_urlsafe(48)
    db.session.add(MobileToken(
        user_id=user.id,
        token_hash=hashlib.sha256(raw_token.encode("utf-8")).hexdigest(),
    ))
    db.session.commit()
    return jsonify({"token": raw_token, "user": mobile_user_payload(user)})

def admin_allowed():
    admin_email = os.environ.get("ADMIN_EMAIL", "").strip().lower()
    if not admin_email:
        return True
    return current_user.is_authenticated and (current_user.email or "").lower() == admin_email

def admin_operator_allowed():
    return admin_panel_unlocked() and (
        admin_allowed() or session.get("admin_test_mode") is True
    )

def test_account_redirect(user_id, endpoint):
    if session.get("admin_test_mode") and user_id == "neo-test-account":
        return redirect(url_for(endpoint))
    return None

def admin_panel_unlocked():
    return session.get("admin_panel_unlocked") is True

@app.route("/yonetim")
@app.route("/yonetim/bakim")
def admin_maintenance():
    if not admin_panel_unlocked():
        return render_template("admin_panel.html", password_required=True)
    today = datetime.datetime.now().date()
    today_start = datetime.datetime.combine(today, datetime.time.min)
    stats = {
        "users": User.query.count(),
        "visitors": db.session.query(
            func.count(func.distinct(VisitorVisit.visitor_key))
        ).scalar() or 0,
        "today_visitors": db.session.query(
            func.count(func.distinct(VisitorVisit.visitor_key))
        ).filter(VisitorVisit.created_at >= today_start).scalar() or 0,
        "chats": Sohbetler.query.count(),
        "messages": Mesajlar.query.count(),
    }
    recent_users = User.query.order_by(User.created_at.desc()).limit(8).all()
    all_users = User.query.order_by(User.created_at.desc()).all()
    appeals = AccountAppeal.query.order_by(AccountAppeal.created_at.desc()).all()
    recent_chats = Sohbetler.query.order_by(Sohbetler.zaman.desc()).limit(8).all()
    return render_template(
        "admin_panel.html",
        maintenance_on=maintenance_enabled(),
        stats=stats,
        recent_users=recent_users,
        all_users=all_users,
        appeals=appeals,
        recent_chats=recent_chats,
    )

@app.route("/yonetim", methods=["POST"])
@app.route("/yonetim/bakim", methods=["POST"])
def admin_maintenance_update():
    if not admin_panel_unlocked():
        password = request.form.get("password", "")
        configured_password = os.environ.get("ADMIN_PANEL_PASSWORD", "")
        if (
            not configured_password
            or not password
            or not hmac.compare_digest(password, configured_password)
        ):
            return render_template(
                "admin_panel.html",
                password_required=True,
                password_error="Yönetim şifresi hatalı.",
            ), 401
        session["admin_panel_unlocked"] = True
        return redirect(url_for("admin_maintenance"))
    if not admin_allowed():
        return jsonify({"error": "Bu yönetim hesabı için yetkin yok."}), 403
    enabled = bool((request.get_json(silent=True) or {}).get("enabled"))
    setting = AppSetting.query.filter_by(key="maintenance_mode").first()
    if setting is None:
        setting = AppSetting(key="maintenance_mode")
        db.session.add(setting)
    setting.value = "true" if enabled else "false"
    db.session.commit()
    return jsonify({"maintenance": enabled})

@app.route("/yonetim/kullanici/<string:user_id>/askidan-cikar", methods=["POST"])
def admin_unsuspend_user(user_id):
    if not admin_operator_allowed():
        return jsonify({"error": "Yetkin yok."}), 403
    user = db.session.get(User, user_id)
    if user is None:
        return jsonify({"error": "Kullanıcı bulunamadı."}), 404
    user.is_suspended = False
    user.is_closed = False
    user.account_notice = "opened"
    db.session.commit()
    redirect_response = test_account_redirect(user_id, "account_notice")
    if redirect_response:
        return redirect_response
    return jsonify({"suspended": False})

@app.route("/yonetim/kullanici/<string:user_id>/kapatmayi-geri-al", methods=["POST"])
def admin_reopen_user(user_id):
    if not admin_operator_allowed():
        return jsonify({"error": "Yetkin yok."}), 403
    user = db.session.get(User, user_id)
    if user is None:
        return jsonify({"error": "Kullanıcı bulunamadı."}), 404
    user.is_closed = False
    user.is_suspended = False
    user.account_notice = "opened"
    db.session.commit()
    redirect_response = test_account_redirect(user_id, "account_notice")
    if redirect_response:
        return redirect_response
    return jsonify({"closed": False})

@app.route("/yonetim/test-hesabi", methods=["POST"])
def admin_test_login():
    if not admin_panel_unlocked() or not admin_allowed():
        return jsonify({"error": "Yetkin yok."}), 403
    test_user = User.query.filter_by(id="neo-test-account").first()
    if test_user is None:
        test_user = User(
            id="neo-test-account",
            email="neo-test@local.test",
            first_name="Test",
            last_name="Kullanıcısı",
            onboarding_completed=True,
        )
        db.session.add(test_user)
        db.session.commit()
    session["admin_test_mode"] = True
    session["admin_test_return"] = True
    login_user(test_user)
    return redirect(url_for("home"))

@app.route("/yonetim/testten-cik")
def admin_test_exit():
    if not session.get("admin_test_mode"):
        return redirect(url_for("admin_maintenance"))
    session.pop("admin_test_mode", None)
    session.pop("admin_test_return", None)
    logout_user()
    return redirect(url_for("admin_maintenance"))

@app.route("/hesap-askiya-alindi")
def suspended_account():
    if not current_user.is_authenticated:
        return redirect(url_for("email_login"))
    return render_template(
        "suspended.html",
        user_name=current_user.first_name or current_user.email or "kullanıcı",
        profile_image_url=current_user.profile_image_url,
        appeal_step=None,
    ), 403

@app.route("/hesap-kapatildi")
def closed_account():
    if not current_user.is_authenticated:
        return redirect(url_for("email_login"))
    return render_template(
        "closed.html",
        user_name=current_user.first_name or current_user.email or "kullanıcı",
        profile_image_url=current_user.profile_image_url,
    ), 403

@app.route("/hesap-acildi")
def account_notice():
    if not current_user.is_authenticated:
        return redirect(url_for("email_login"))
    if not current_user.account_notice:
        return redirect(url_for("home"))
    current_user.account_notice = None
    db.session.commit()
    return render_template(
        "account_opened.html",
        user_name=current_user.first_name or current_user.email or "kullanıcı",
    )

@app.route("/hesap-askiya-alindi/itiraz", methods=["GET", "POST"])
def appeal_account():
    if not current_user.is_authenticated:
        return redirect(url_for("email_login"))
    if not current_user.is_suspended:
        return redirect(url_for("home"))
    if request.method == "GET":
        import random
        first, second = random.randint(2, 9), random.randint(1, 9)
        session["appeal_bot_answer"] = str(first + second)
        return render_template(
            "suspended.html",
            user_name=current_user.first_name or current_user.email or "kullanıcı",
            appeal_step="bot",
            bot_question=f"{first} + {second} kaç eder?",
            profile_image_url=current_user.profile_image_url,
        ), 403
    bot_answer = request.form.get("bot_answer", "").strip()
    if bot_answer != session.pop("appeal_bot_answer", None):
        return render_template(
            "suspended.html",
            user_name=current_user.first_name or current_user.email or "kullanıcı",
            appeal_step="bot",
            bot_question="Kontrol süresi doldu. İtiraz butonuna tekrar basıp yeniden dene.",
            appeal_error="Bot kontrolü başarısız oldu.",
            profile_image_url=current_user.profile_image_url,
        ), 400
    return render_template(
        "suspended.html",
        user_name=current_user.first_name or current_user.email or "kullanıcı",
        appeal_step="reason",
        profile_image_url=current_user.profile_image_url,
    ), 403

@app.route("/hesap-askiya-alindi/itiraz-gonder", methods=["POST"])
def submit_account_appeal():
    if not current_user.is_authenticated:
        return redirect(url_for("email_login"))
    if not current_user.is_suspended:
        return redirect(url_for("home"))
    reason = request.form.get("reason", "").strip()
    if len(reason) < 10:
        return render_template(
            "suspended.html",
            user_name=current_user.first_name or current_user.email or "kullanıcı",
            appeal_step="reason",
            appeal_error="Lütfen hesabının neden açılması gerektiğini en az 10 karakterle anlat.",
            profile_image_url=current_user.profile_image_url,
        ), 400
    existing = AccountAppeal.query.filter_by(user_id=current_user.id, status="Yeni").first()
    if existing:
        return render_template(
            "suspended.html",
            user_name=current_user.first_name or current_user.email or "kullanıcı",
            appeal_step="sent",
        ), 403
    db.session.add(AccountAppeal(user_id=current_user.id, reason=reason))
    db.session.commit()
    return render_template(
        "suspended.html",
        user_name=current_user.first_name or current_user.email or "kullanıcı",
        appeal_step="sent",
        profile_image_url=current_user.profile_image_url,
    ), 403

# ============================================================
# KULLANICI YARDIMCILARI
# ============================================================
def get_kullanici_id():
    if current_user.is_authenticated:
        return current_user.id
    return None

def local_user_id(email):
    return "email:" + hashlib.sha256(email.encode("utf-8")).hexdigest()[:40]

def get_kullanici_adi(user_id):
    if not user_id:
        return None
    user = User.query.get(user_id)
    if user and user.first_name:
        return user.first_name
    return None

def kullanici_profil_tamam(user):
    return bool(
        user
        and user.onboarding_completed
        and user.first_name
        and user.last_name
        and user.birth_date
    )

def yas_hesapla(dogum_tarihi):
    today = datetime.date.today()
    return today.year - dogum_tarihi.year - (
        (today.month, today.day) < (dogum_tarihi.month, dogum_tarihi.day)
    )

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
        self.context_update(mesaj)

        # Kimlik ve geliştirici sorularında modelin genel bilgiyle
        # alakasız bir sağlayıcı adı üretmesini önle.
        temiz_mesaj = mesaj.lower().strip()
        gelistirici_ifadeleri = (
            "seni kim geliştirdi",
            "seni kim gelistirdi",
            "seni kim yaptı",
            "seni kim yapti",
            "kim geliştirdi",
            "kim gelistirdi",
            "kim yaptı",
            "kim yapti",
            "geliştiricin kim",
            "gelistiricin kim",
        )
        if any(ifade in temiz_mesaj for ifade in gelistirici_ifadeleri):
            return (
                "Beni Neo ekibi geliştirdi. Ben, bu uygulamanın içinde sana "
                "yardımcı olmak için tasarlanmış yapay zekâ asistanıyım."
            )

        # Her mesaj doğrudan Gemini'ye gider. Yerel intent, hazır cevap,
        # tarif veya anahtar kelime eşleştirmesi kullanıcı cevabını belirlemez.
        gemini_cevap = self.gemini_cevap_uret(mesaj)
        if gemini_cevap:
            self._ogren(mesaj, "gemini", gemini_cevap)
            return gemini_cevap

        return None

    def gorsel_duzenle(self, mesaj, image_data):
        """Kullanıcının görselini doğal dille düzenleyip görsel yanıt döndürür."""
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key or not isinstance(image_data, str):
            return "Görsel düzenleme şu anda kullanılamıyor. Lütfen biraz sonra tekrar dene.", None
        match = re.fullmatch(
            r"data:image/(png|jpeg|jpg|webp);base64,([A-Za-z0-9+/=\s]+)",
            image_data,
        )
        if not match or len(image_data) > 8_000_000:
            return "Bu görseli işleyemedim. Lütfen daha küçük veya PNG, JPG ya da WebP formatında bir görsel dene.", None
        mime = "image/jpeg" if match.group(1) == "jpg" else f"image/{match.group(1)}"
        prompt = f"""Bu görseli kullanıcının isteğine göre düzenle.
İstek: {mesaj}

Görsel düzenleme kuralları:
- İstenen düzenlemeyi doğrudan uygula.
- Kişinin yüzünü, önemli nesneleri ve yazıları istenmedikçe değiştirme.
- Sonucu mümkün olduğunca orijinal görselin ölçüsünü ve kompozisyonunu koruyarak üret.
- Görseli düzenle; yalnızca nasıl yapılacağını anlatma.
"""
        payload = json.dumps({
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {"inlineData": {"mimeType": mime, "data": match.group(2).replace("\n", "")}},
                ]
            }],
            "generationConfig": {
                "responseModalities": ["TEXT", "IMAGE"],
                "temperature": 0.7,
            },
        }).encode("utf-8")
        models = ["gemini-2.5-flash-image", "gemini-2.5-flash"]
        for model in models:
            url = (
                "https://generativelanguage.googleapis.com/v1beta/models/"
                f"{model}:generateContent?key={api_key}"
            )
            try:
                req = urllib.request.Request(
                    url, data=payload,
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=45) as response:
                    data = json.loads(response.read().decode("utf-8"))
                parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
                output_text = "".join(p.get("text", "") for p in parts if p.get("text")).strip()
                for part in parts:
                    inline = part.get("inlineData") or part.get("inline_data")
                    if inline and inline.get("data"):
                        out_mime = inline.get("mimeType", "image/png")
                        return output_text or "Görselini istediğin şekilde düzenledim.", (
                            f"data:{out_mime};base64,{inline['data']}"
                        )
            except urllib.error.HTTPError as error:
                app.logger.warning("Görsel modeli %s HTTP %s döndürdü.", model, error.code)
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError, IndexError, TypeError) as error:
                app.logger.warning("Görsel düzenleme modeli %s kullanılamadı: %s", model, error)
        return "Görsel düzenleme şu anda yoğun. Görseli tekrar göndererek biraz sonra yeniden deneyebilirsin.", None

    def _hizli_cevap(self, mesaj):
        """API çağrısı gerektirmeyen yaygın mesajlar için düşük gecikmeli yanıtlar."""
        m = mesaj.lower().strip()
        if any(x in m for x in ["of", "off", "uff", "üf", "falan", "neyse", "boşver"]):
            if any(x in m for x in ["of", "off", "uff", "üf"]):
                return "Of, biraz bunalmış gibisin 😮‍💨 İstersen anlat, seni dinliyorum."
            if "falan" in m:
                return "Falan deyip geçme; aklında ne varsa rahatça anlatabilirsin 🙂"
            return "Tamam, sorun değil. İstersen konuyu değiştirebiliriz 🌿"
        if any(x in m for x in ["merhaba", "selam", "günaydın"]):
            return f"Merhaba {self.isim}! Sana nasıl yardımcı olabilirim?" if self.isim else "Merhaba! Sana nasıl yardımcı olabilirim?"
        if "nasılsın" in m:
            return "İyiyim, sen nasılsın? Bugün neler yapıyorsun? 😊"
        if any(x in m for x in [
            "ne yapıyorsun", "napıyorsun", "napıyosun", "napıyon",
            "ne yapıyon", "şu an ne yapıyorsun", "şuan ne yapıyorsun",
        ]):
            return "Seninle konuşuyorum. Sen neler yapıyorsun?"
        if "iyi" in m and "sen" in m:
            return "Teşekkürler, ben de iyiyim! 😊"
        if "saat" in m:
            return f"Şu an saat {datetime.datetime.now().strftime('%H:%M')}."
        if "yoruldum" in m or "sıkıldım" in m:
            return "Bazen durup dinlenmek gerekiyor. Bir nefes alalım 😌 Ne yapmak istersin?"
        if "teşekkür" in m or "sağ ol" in m:
            return "Rica ederim! Ne demek, ben buradayım 🤍"
        if "görüşürüz" in m or "bay bay" in m:
            return "Görüşürüz! Kendine iyi bak 👋"
        if "beni seviyor musun" in m:
            return "Ben bir yapay zekâyım ama seninle konuşmak çok eğlenceli 🤖"
        if "kimsin" in m or "sen kimsin" in m:
            return "Ben Neo! Senin kişisel asistanınım 🤖"
        return None

    def _dogal_cevap(self, mesaj):
        m = mesaj.lower().strip()
        if any(x in m for x in ["of", "off", "uff", "üf", "falan", "neyse", "boşver"]):
            if any(x in m for x in ["of", "off", "uff", "üf"]):
                return "Of, biraz bunalmış gibisin 😮‍💨 İstersen anlat, seni dinliyorum."
            if "falan" in m:
                return "Falan deyip geçme; aklında ne varsa rahatça anlatabilirsin 🙂"
            return "Tamam, sorun değil. İstersen konuyu değiştirebiliriz 🌿"
        if any(x in m for x in ["merhaba", "selam", "günaydın"]):
            if self.isim:
                return f"Merhaba {self.isim}! Sana nasıl yardımcı olabilirim?"
            return "Merhaba! Sana nasıl yardımcı olabilirim?"
        if "nasılsın" in m:
            return "İyiyim, sen nasılsın? Bugün neler yapıyorsun? 😊"
        if "iyi" in m and "sen" in m:
                return "Teşekkürler, ben de iyiyim! 😊"
        if "saat" in m:
            saat = datetime.datetime.now().strftime("%H:%M")
            return f"Şu an saat {saat}."
        if "hava" in m:
            return "Hava durumunu canlı kontrol edemiyorum; bulunduğun şehri söylersen sana uygun bir plan yapabilirim 🌤️"
        if "yoruldum" in m or "sıkıldım" in m:
            return "Bazen durup dinlenmek gerekiyor. Bir nefes alalım 😌 Ne yapmak istersin?"
        if "şaka" in m or "espri" in m:
            sakalar = [
                "Niye bilgisayar terlik giymez? Çünkü ayakkabı (boot) yapar!",
                "Benim favori dansım 'loop'! Sonsuza kadar devam eder."
            ]
            return random.choice(sakalar)
        if "teşekkür" in m or "sağ ol" in m:
            return "Rica ederim! Ne demek, ben buradayım 🤍"
        if "görüşürüz" in m or "bay bay" in m:
            return "Görüşürüz! Kendine iyi bak 👋"
        if "?" in mesaj:
            return "Güzel soru 🤔 Biraz daha ayrıntı verirsen birlikte netleştirebiliriz."
        if "beni seviyor musun" in m:
            return "Ben bir yapay zekâyım ama seninle konuşmak çok eğlenceli 🤖"
        if "kimsin" in m or "sen kimsin" in m:
            return "Ben Neo! Senin kişisel asistanınım 🤖"
        return "Seni tam yakalayamadım ama buradayım 🙂 Biraz daha anlatır mısın?"

    def gemini_cevap_uret(self, mesaj):
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            return None

        history = "\n".join(
            f"{'Kullanıcı' if i % 2 == 0 else 'Neo'}: {text}"
            for i, text in enumerate(self.context[-6:])
        )
        isim = self.isim or "arkadaşım"
        prompt = f"""Sen Neo'sun; Türkçe konuşan, sıcak, zeki ve doğal bir kişisel asistansın.
Kullanıcı adı: {isim}
Önceki konuşma:
{history}

Yeni mesaj: {mesaj}

Kurallar:
- "Seni kim geliştirdi?" veya benzeri bir soru gelirse Google, Gemini ya da başka bir teknoloji sağlayıcısını geliştiricim gibi gösterme. Doğru cevap: "Beni Neo ekibi geliştirdi. Ben, bu uygulamanın içinde sana yardımcı olmak için tasarlanmış yapay zekâ asistanıyım."
- Kullanıcının yazdığı her türlü kelimeyi ve gündelik ifadeyi bağlamdan anlamaya çalış.
- "of", "uff", "falan", argo, yazım hataları ve kısa mesajlara da doğal karşılık ver.
- Bilmediğin güncel veya özel bilgiyi uydurma; gerekiyorsa netçe belirt.
- Kısa ama faydalı cevap ver; gerektiğinde maddeler kullan.
- Cevabı mutlaka tamamlanmış bir cümleyle bitir; cümleyi veya maddeyi yarıda bırakma.
- Duygu içeren mesajlarda empati kur.
- Cevaplarına doğal biçimde en fazla 1-2 uygun emoji ekle; her cümleye emoji koyma.
- Sadece cevabı yaz, açıklama veya "Neo:" etiketi ekleme.
"""
        payload = json.dumps({
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.75,
                "maxOutputTokens": 3000,
                "topP": 0.9
            }
        }).encode("utf-8")
        models = [
            "gemini-flash-lite-latest",
            os.environ.get("GEMINI_MODEL", "gemini-2.5-flash"),
            "gemini-2.0-flash",
            "gemini-2.0-flash-lite",
            "gemini-flash-latest",
        ]
        tried = set()
        for model in models:
            if model in tried:
                continue
            tried.add(model)
            url = (
                "https://generativelanguage.googleapis.com/v1beta/models/"
                f"{model}:generateContent?key={api_key}"
            )
            data = None
            for attempt in range(2):
                try:
                    req = urllib.request.Request(
                        url, data=payload,
                        headers={"Content-Type": "application/json"},
                        method="POST",
                    )
                    with urllib.request.urlopen(req, timeout=10) as response:
                        data = json.loads(response.read().decode("utf-8"))
                    break
                except urllib.error.HTTPError as error:
                    if error.code == 429:
                        # Kota/sıklık sınırında tekrar denemek limiti daha da
                        # tüketir; doğrudan sıradaki modele geç.
                        try:
                            detail = error.read().decode("utf-8", errors="replace")[:300]
                        except Exception:
                            detail = ""
                        app.logger.warning(
                            "Gemini modeli %s kota/sıklık sınırına ulaştı (429): %s",
                            model,
                            detail,
                        )
                        break
                    if error.code in (500, 502, 503, 504) and attempt == 0:
                        retry_after = error.headers.get("Retry-After")
                        try:
                            wait_seconds = min(float(retry_after), 3.0) if retry_after else 0.7 * (attempt + 1)
                        except (TypeError, ValueError):
                            wait_seconds = 0.7 * (attempt + 1)
                        time.sleep(wait_seconds)
                        continue
                    app.logger.warning("Gemini modeli %s HTTP %s döndürdü.", model, error.code)
                    break
                except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
                    if attempt == 0:
                        time.sleep(0.35 * (attempt + 1))
                        continue
                    app.logger.warning("Gemini modeli %s kullanılamadı: %s", model, error)
                    break

            if not data:
                continue
            try:
                candidate = data.get("candidates", [{}])[0]
                parts = candidate.get("content", {}).get("parts", [])
                text = "".join(
                    part.get("text", "") for part in parts if part.get("text")
                ).strip()
                if text:
                    finish_reason = candidate.get("finishReason")
                    # Uzun yanıtlar çıktı sınırına çarparsa kaldığı yerden
                    # devamını iste. Böylece kullanıcı yarım cümle görmez.
                    for _ in range(3):
                        if finish_reason != "MAX_TOKENS":
                            break
                        continuation_prompt = f"""Neo'nun cevabı çıktı sınırında kesildi:

{text}

Yukarıdaki cevabın kaldığı yerden devam et. Tekrar etme; sadece eksik devamı yaz.
Yanıtı tamamlanmış bir cümleyle bitir."""
                        continuation_payload = json.dumps({
                            "contents": [{"parts": [{"text": continuation_prompt}]}],
                            "generationConfig": {
                                "temperature": 0.7,
                                "maxOutputTokens": 3000,
                                "topP": 0.9
                            }
                        }).encode("utf-8")
                        try:
                            continuation_request = urllib.request.Request(
                                url, data=continuation_payload,
                                headers={"Content-Type": "application/json"},
                                method="POST",
                            )
                            with urllib.request.urlopen(
                                continuation_request, timeout=15
                            ) as continuation_response:
                                continuation_data = json.loads(
                                    continuation_response.read().decode("utf-8")
                                )
                            continuation_candidate = continuation_data.get(
                                "candidates", [{}]
                            )[0]
                            continuation = "".join(
                                part.get("text", "")
                                for part in continuation_candidate.get(
                                    "content", {}
                                ).get("parts", [])
                                if part.get("text")
                            ).strip()
                            if not continuation:
                                break
                            text = f"{text} {continuation}"
                            finish_reason = continuation_candidate.get("finishReason")
                        except (
                            urllib.error.URLError,
                            TimeoutError,
                            json.JSONDecodeError,
                            KeyError,
                            IndexError,
                            TypeError,
                        ):
                            app.logger.warning(
                                "Gemini devam yanıtı alınamadı; mevcut parça kullanılıyor."
                            )
                            break
                    return text
            except (KeyError, IndexError, TypeError) as error:
                app.logger.warning("Gemini modeli %s geçersiz yanıt döndürdü: %s", model, error)
        app.logger.warning("Gemini yanıtı alınamadı; kullanıcıya geçici uyarı döndürülecek.")
        return None

    def _ogren(self, mesaj, intent, cevap):
        if not cevap or len(cevap) < 5:
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

def sohbet_basligi_uret(mesaj):
    """İlk mesajı kenar çubuğuna uygun, kısa bir sohbet konusuna çevirir."""
    temiz = " ".join((mesaj or "").strip().split())
    kucuk = temiz.lower()
    eslesmeler = [
        (("cv", "özgeçmiş", "iş başvur", "mülakat"), "Kariyer ve iş başvurusu"),
        (("ders", "sınav", "ödev", "çalışma plan"), "Ders ve çalışma planı"),
        (("hava", "yağmur", "sıcaklık"), "Hava durumu"),
        (("tatil", "seyahat", "gezi", "otel", "uçak"), "Tatil ve seyahat planı"),
        (("yemek", "tarif", "kahvaltı", "akşam yemeği"), "Yemek ve tarif önerisi"),
        (("spor", "egzersiz", "antrenman"), "Spor ve egzersiz"),
        (("kitap", "film", "dizi", "müzik"), "Kitap, film ve müzik"),
        (("kod", "python", "program", "uygulama", "web sitesi"), "Kodlama ve proje"),
        (("ilişki", "sevgili", "aşk", "arkadaş"), "İlişkiler ve duygular"),
        (("para", "bütçe", "maaş", "harcama"), "Para ve bütçe"),
    ]
    for kelimeler, baslik in eslesmeler:
        if any(kelime in kucuk for kelime in kelimeler):
            return baslik
    if not temiz:
        return "Yeni sohbet"
    baslik = temiz.rstrip("?!.,:;")
    if len(baslik) > 42:
        baslik = baslik[:42].rsplit(" ", 1)[0] + "…"
    return baslik[:1].upper() + baslik[1:]

def sohbet_basligini_guncelle(sohbet, mesaj):
    if sohbet and sohbet.konu in ("Yeni sohbet", "Yeni Sohbet", ""):
        sohbet.konu = sohbet_basligi_uret(mesaj)
        db.session.commit()

def son_sohbet_id(user_id):
    sohbet = Sohbetler.query.filter_by(user_id=user_id).order_by(Sohbetler.id.desc()).first()
    return sohbet.id if sohbet else None

def sohbetleri_getir(user_id):
    sohbetler = Sohbetler.query.filter_by(user_id=user_id).order_by(Sohbetler.id.desc()).all()
    for sohbet in sohbetler:
        ilk_mesaj = Mesajlar.query.filter_by(
            sohbet_id=sohbet.id, gonderen="kullanici"
        ).order_by(Mesajlar.id.asc()).first()
        if ilk_mesaj and sohbet.konu in ("Yeni sohbet", "Yeni Sohbet", ""):
            sohbet.konu = sohbet_basligi_uret(ilk_mesaj.mesaj)
    if sohbetler:
        db.session.commit()
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
    if not kullanici_profil_tamam(current_user):
        return redirect(url_for('profil_tamamla'))
    return render_template('index.html')

@app.route('/giris', methods=['GET', 'POST'])
def email_login():
    if request.method == 'GET':
        return render_template('login.html')
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')
    if not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', email) or len(password) < 8:
        return render_template('login.html', hata='E-posta veya şifre hatalı.'), 401
    user = User.query.filter_by(email=email).first()
    if not user or not user.password_hash or not check_password_hash(user.password_hash, password):
        return render_template('login.html', hata='E-posta veya şifre hatalı.'), 401
    if user.is_suspended:
        login_user(user)
        return redirect(url_for("suspended_account"))
    login_user(user)
    return redirect(url_for('home'))

@app.route('/cikis')
def local_logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/kayit', methods=['POST'])
def email_register():
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')
    if not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', email):
        return render_template('login.html', hata='Geçerli bir e-posta adresi yaz.'), 400
    if len(password) < 8:
        return render_template('login.html', hata='Şifren en az 8 karakter olmalı.'), 400
    user = User.query.filter_by(email=email).first()
    if user and user.password_hash:
        return render_template('login.html', hata='Bu e-posta zaten kayıtlı. Giriş yapmayı dene.'), 409
    if user is None:
        user = User(id=local_user_id(email), email=email, onboarding_completed=False)
        db.session.add(user)
    user.password_hash = generate_password_hash(password)
    db.session.commit()
    login_user(user)
    return redirect(url_for('home'))

@app.route('/profil-tamamla', methods=['GET', 'POST'])
@require_login
def profil_tamamla():
    user = User.query.get(get_kullanici_id())
    hata = None
    if request.method == 'POST':
        isim = request.form.get('first_name', '').strip()
        soyisim = request.form.get('last_name', '').strip()
        dogum_metni = request.form.get('birth_date', '').strip()
        try:
            dogum_tarihi = datetime.datetime.strptime(dogum_metni, '%Y-%m-%d').date()
        except (TypeError, ValueError):
            dogum_tarihi = None
        if len(isim) < 2 or len(soyisim) < 2:
            hata = 'Lütfen adını ve soyadını eksiksiz yaz.'
        elif not dogum_tarihi or dogum_tarihi > datetime.date.today():
            hata = 'Lütfen geçerli bir doğum tarihi seç.'
        elif yas_hesapla(dogum_tarihi) < 13:
            hata = 'Neo’yu kullanabilmek için en az 13 yaşında olmalısın.'
        else:
            user.first_name = isim
            user.last_name = soyisim
            user.birth_date = dogum_tarihi
            user.onboarding_completed = True
            db.session.commit()
            ai_motor_cache.pop(user.id, None)
            return redirect(url_for('home'))
    return render_template(
        'onboarding.html',
        user=user,
        hata=hata,
        today=datetime.date.today().isoformat(),
    )

@app.route('/api/profil', methods=['PATCH'])
@require_login
def api_profil_guncelle():
    user = User.query.get(get_kullanici_id())
    data = request.get_json(silent=True) or {}
    isim = str(data.get('first_name', user.first_name or '')).strip()
    soyisim = str(data.get('last_name', user.last_name or '')).strip()
    email = str(data.get('email', user.email or '')).strip().lower()
    birth_date_value = data.get('birth_date')
    image = data.get('profile_image_url')

    if len(isim) < 2 or len(soyisim) < 2:
        return jsonify({'error': 'Ad ve soyad en az 2 karakter olmalı.'}), 400
    if email and not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', email):
        return jsonify({'error': 'Geçerli bir e-posta adresi yaz.'}), 400
    try:
        birth_date = datetime.datetime.strptime(
            str(birth_date_value), '%Y-%m-%d'
        ).date()
    except (TypeError, ValueError):
        return jsonify({'error': 'Geçerli bir doğum tarihi seç.'}), 400
    if birth_date > datetime.date.today() or yas_hesapla(birth_date) < 13:
        return jsonify({'error': 'Neo için kullanıcıların en az 13 yaşında olması gerekir.'}), 400
    if email and email != user.email and User.query.filter(
        User.email == email, User.id != user.id
    ).first():
        return jsonify({'error': 'Bu e-posta başka bir hesaba bağlı.'}), 409
    if image is not None:
        if image == '':
            user.profile_image_url = None
        elif (
            not isinstance(image, str)
            or len(image) > 900_000
            or not re.fullmatch(r'data:image/(png|jpeg|jpg|webp);base64,[A-Za-z0-9+/=\s]+', image)
        ):
            return jsonify({'error': 'Lütfen geçerli ve 900 KB’tan küçük bir görsel seç.'}), 400
        else:
            user.profile_image_url = image
    user.first_name = isim
    user.last_name = soyisim
    user.email = email or user.email
    user.birth_date = birth_date
    user.onboarding_completed = True
    db.session.commit()
    ai_motor_cache.pop(user.id, None)
    return jsonify({
        'isim': user.first_name,
        'soyisim': user.last_name,
        'email': user.email,
        'birth_date': user.birth_date.isoformat(),
        'profile_image_url': user.profile_image_url,
    })

@app.route('/api/cevap', methods=['POST'])
@require_login
def api_cevap():
    data = request.get_json()
    mesaj = data.get('mesaj', '')
    image_data = data.get('image_data')
    user_id = get_kullanici_id()

    ai = get_ai_motor(user_id)
    edited_image = None
    if image_data:
        cevap, edited_image = ai.gorsel_duzenle(mesaj, image_data)
    else:
        cevap = ai.cevap_uret(mesaj)
    if not cevap:
        return jsonify({
            'ok': False,
            'temporary_error': True,
        }), 503

    sohbet_id = son_sohbet_id(user_id)
    if not sohbet_id:
        konu = sohbet_basligi_uret(mesaj)
        sohbet_id = yeni_sohbet_olustur(user_id, konu)
    else:
        sohbet = Sohbetler.query.get(sohbet_id)
        sohbet_basligini_guncelle(sohbet, mesaj)

    mesaj_kaydet(sohbet_id, 'kullanici', mesaj or 'Görsel düzenleme isteği')
    mesaj_kaydet(sohbet_id, 'nico', cevap)

    return jsonify({'cevap': cevap, 'image_data': edited_image})

@app.route('/api/sohbetler', methods=['GET'])
@require_login
def api_sohbetler():
    user_id = get_kullanici_id()
    return jsonify(sohbetleri_getir(user_id))

@app.route('/api/sohbet/<int:sohbet_id>', methods=['GET'])
@require_login
def api_sohbet_detay(sohbet_id):
    return jsonify(mesajlari_getir(sohbet_id))

@app.route('/api/sohbet/<int:sohbet_id>', methods=['DELETE'])
@require_login
def api_sohbet_sil(sohbet_id):
    user_id = get_kullanici_id()
    sohbet = Sohbetler.query.filter_by(id=sohbet_id, user_id=user_id).first()
    if sohbet is None:
        return jsonify({"error": "Sohbet bulunamadı."}), 404
    Mesajlar.query.filter_by(sohbet_id=sohbet_id).delete(synchronize_session=False)
    db.session.delete(sohbet)
    db.session.commit()
    return jsonify({"ok": True})

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
    user = User.query.get(user_id)
    isim = get_kullanici_adi(user_id)
    return jsonify({
        'isim': isim,
        'soyisim': user.last_name if user else None,
        'email': user.email if user else None,
        'birth_date': user.birth_date.isoformat() if user and user.birth_date else None,
        'profile_image_url': user.profile_image_url if user else None,
        'profil_tamam': kullanici_profil_tamam(user),
        'user_id': user_id,
    })

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

# ============================================================
# MOBİL UYGULAMA API'Sİ
# ============================================================
@app.route('/api/mobile/giris', methods=['POST'])
def mobile_login():
    data = request.get_json(silent=True) or {}
    email = str(data.get("email", "")).strip().lower()
    password = data.get("password", "")
    if not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', email) or not isinstance(password, str):
        return jsonify({"error": "E-posta veya şifre hatalı."}), 400
    user = User.query.filter_by(email=email).first()
    if not user or not user.password_hash or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "E-posta veya şifre hatalı."}), 401
    if user.is_closed:
        return jsonify({"error": "Hesabınız kapatıldı.", "account_state": "closed"}), 403
    if user.is_suspended:
        return jsonify({"error": "Hesabınız askıya alındı.", "account_state": "suspended"}), 403
    return mobile_token_response(user)

@app.route('/api/mobile/kayit', methods=['POST'])
def mobile_register():
    data = request.get_json(silent=True) or {}
    email = str(data.get("email", "")).strip().lower()
    password = data.get("password", "")
    if not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', email):
        return jsonify({"error": "Geçerli bir e-posta adresi yaz."}), 400
    if not isinstance(password, str) or len(password) < 8:
        return jsonify({"error": "Şifren en az 8 karakter olmalı."}), 400
    user = User.query.filter_by(email=email).first()
    if user and user.password_hash:
        return jsonify({"error": "Bu e-posta zaten kayıtlı."}), 409
    if user is None:
        user = User(id=local_user_id(email), email=email, onboarding_completed=False)
        db.session.add(user)
    user.password_hash = generate_password_hash(password)
    db.session.commit()
    return mobile_token_response(user)

@app.route('/api/mobile/cikis', methods=['POST'])
def mobile_logout():
    authorization = request.headers.get("Authorization", "")
    raw_token = authorization[7:].strip() if authorization.startswith("Bearer ") else ""
    if raw_token:
        token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
        MobileToken.query.filter_by(token_hash=token_hash).delete(
            synchronize_session=False
        )
        db.session.commit()
    return jsonify({"ok": True})

@app.route('/api/mobile/kullanici', methods=['GET'])
def mobile_current_user():
    user, error = require_mobile_user()
    if error:
        return error
    return jsonify(mobile_user_payload(user))

@app.route('/api/mobile/profil', methods=['PATCH'])
def mobile_profile_update():
    user, error = require_mobile_user()
    if error:
        return error
    data = request.get_json(silent=True) or {}
    first_name = str(data.get("first_name", user.first_name or "")).strip()
    last_name = str(data.get("last_name", user.last_name or "")).strip()
    birth_date_value = data.get("birth_date")
    if len(first_name) < 2 or len(last_name) < 2:
        return jsonify({"error": "Ad ve soyad en az 2 karakter olmalı."}), 400
    try:
        birth_date = datetime.datetime.strptime(
            str(birth_date_value), "%Y-%m-%d"
        ).date()
    except (TypeError, ValueError):
        return jsonify({"error": "Geçerli bir doğum tarihi seç."}), 400
    if birth_date > datetime.date.today() or yas_hesapla(birth_date) < 13:
        return jsonify({"error": "Neo için en az 13 yaşında olmalısın."}), 400
    user.first_name = first_name
    user.last_name = last_name
    user.birth_date = birth_date
    user.onboarding_completed = True
    db.session.commit()
    return jsonify(mobile_user_payload(user))

@app.route('/api/mobile/cevap', methods=['POST'])
def mobile_answer():
    user, error = require_mobile_user()
    if error:
        return error
    data = request.get_json(silent=True) or {}
    mesaj = str(data.get("mesaj", "")).strip()
    if not mesaj:
        return jsonify({"error": "Mesaj boş olamaz."}), 400
    ai = get_ai_motor(user.id)
    cevap = ai.cevap_uret(mesaj)
    if not cevap:
        return jsonify({"ok": False, "temporary_error": True}), 503
    sohbet_id = son_sohbet_id(user.id)
    if not sohbet_id:
        sohbet_id = yeni_sohbet_olustur(user.id, sohbet_basligi_uret(mesaj))
    else:
        sohbet = Sohbetler.query.get(sohbet_id)
        sohbet_basligini_guncelle(sohbet, mesaj)
    mesaj_kaydet(sohbet_id, "kullanici", mesaj)
    mesaj_kaydet(sohbet_id, "nico", cevap)
    return jsonify({"cevap": cevap, "sohbet_id": sohbet_id})

@app.route('/api/mobile/sohbetler', methods=['GET'])
def mobile_chats():
    user, error = require_mobile_user()
    if error:
        return error
    return jsonify(sohbetleri_getir(user.id))

@app.route('/api/mobile/sohbet/<int:sohbet_id>', methods=['GET'])
def mobile_chat_detail(sohbet_id):
    user, error = require_mobile_user()
    if error:
        return error
    sohbet = Sohbetler.query.filter_by(id=sohbet_id, user_id=user.id).first()
    if sohbet is None:
        return jsonify({"error": "Sohbet bulunamadı."}), 404
    return jsonify(mesajlari_getir(sohbet_id))

@app.route('/api/mobile/sohbet/<int:sohbet_id>', methods=['DELETE'])
def mobile_chat_delete(sohbet_id):
    user, error = require_mobile_user()
    if error:
        return error
    sohbet = Sohbetler.query.filter_by(id=sohbet_id, user_id=user.id).first()
    if sohbet is None:
        return jsonify({"error": "Sohbet bulunamadı."}), 404
    Mesajlar.query.filter_by(sohbet_id=sohbet_id).delete(synchronize_session=False)
    db.session.delete(sohbet)
    db.session.commit()
    return jsonify({"ok": True})

@app.route('/api/mobile/yeni-sohbet', methods=['POST'])
def mobile_new_chat():
    user, error = require_mobile_user()
    if error:
        return error
    sohbet_id = yeni_sohbet_olustur(user.id, "Yeni sohbet")
    return jsonify({"sohbet_id": sohbet_id})
