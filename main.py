import os
from flask import Flask, render_template, request, redirect, url_for, Markup
# Gemini API için kütüphane
from google import genai
from google.genai.errors import APIError

# Flask uygulamasını başlat
app = Flask(__name__)

# Replit Sırlar (Secrets) menüsünden API anahtarını otomatik çeker.
# Anahtar yoksa uygulama çalışmaz.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("HATA: GEMINI_API_KEY bulunamadı. Lütfen Replit Secrets (Sırlar) menüsüne ekleyin.")

# Gemini istemcisini (client) başlat
try:
    client = genai.Client(api_key=GEMINI_API_KEY)
except Exception:
    client = None # Anahtar yoksa Client oluşturulamaz

# ----------------------------------------------------------------------
## 🧠 NICO - Yapay Zeka Sohbet İşlevi
# ----------------------------------------------------------------------

def nico_ile_sohbet_et(sorgu):
    """Gemini API kullanarak gerçek zamanlı sohbet yanıtı üretir."""

    if not client:
        return {"yanit": "NICO şuan çevrimdışı. Lütfen GEMINI_API_KEY anahtarınızı kontrol edin."}

    # Modele bir kişilik ve bağlam veriyoruz (NICO karakteri)
    system_prompt = (
        "Senin adın NICO. Sen, kullanıcılara dostça, bilgilendirici ve espri yapabilen "
        "bir yapay zeka asistanısın. Yanıtlarını Türkçe ve kısa tut."
    )

    try:
        # Gemini modelini çağır
        response = client.models.generate_content(
            model='gemini-2.5-flash', # Hızlı ve güçlü sohbet modeli
            contents=sorgu,
            config=genai.types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.7 # Yaratıcılığı artırır
            )
        )

        return {"yanit": response.text}

    except APIError as e:
        return {"yanit": f"API HATASI: Gemini servisine ulaşılamadı. (Hata: {e})"}
    except Exception as e:
        return {"yanit": f"GENEL HATA: Beklenmedik bir hata oluştu. Detay: {e}"}

# ----------------------------------------------------------------------
## 🖥️ Flask Rotları (Web Adresleri)
# ----------------------------------------------------------------------

@app.route('/')
def anasayfa():
    """Ana sayfa: Sohbet formunu gösterir."""
    return render_template('nico_chat.html', cevap="")

@app.route('/sohbet', methods=['POST'])
def sohbet_rotasi():
    """Formdan gelen sorguyu işler ve NICO ile sohbeti başlatır."""
    sorgu = request.form.get('sorgu')
    if not sorgu:
        return redirect(url_for('anasayfa'))

    # Yapay zeka sohbet işlevi çağrılır
    yanit = nico_ile_sohbet_et(sorgu)

    # Ana sayfaya cevabı gönderir
    return render_template('nico_chat.html', 
                           cevap=yanit['yanit'], 
                           sorgu=sorgu)

# ----------------------------------------------------------------------
## 🚀 Uygulamayı Çalıştır
# ----------------------------------------------------------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
