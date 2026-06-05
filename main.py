import sqlite3
import datetime
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Veritabanı bağlantısı
def mesaj_kaydet(kullanici_mesaji, nico_cevabi):
    conn = sqlite3.connect('nico_hafiza.db')
    cursor = conn.cursor()
    zaman = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('INSERT INTO sohbetler (kullanici_mesaji, nico_cevabi) VALUES (?, ?)', 
                   (kullanici_mesaji, nico_cevabi))
    conn.commit()
    conn.close()

def nico_cevap_ver(mesaj):
    m = mesaj.lower()
    
    # Hafıza kontrol - geçmiş mesajları al
    conn = sqlite3.connect('nico_hafiza.db')
    cursor = conn.cursor()
    cursor.execute('SELECT kullanici_mesaji, nico_cevabi FROM sohbetler ORDER BY id DESC')
    gecmis = cursor.fetchall()
    conn.close()

    # Hafıza: Kullanıcı daha önce adını söylemiş mi?
    kullanici_adi = None
    for k_mesaj, n_cevap in gecmis:
        if "adım" in k_mesaj.lower() and "demiralp" in k_mesaj.lower():
            kullanici_adi = "Demiralp"
            break

    # 0. HAFIZA SORULARI
    if "adım ne" in m or "ben kimim" in m:
        if kullanici_adi:
            cevap = f"Sen {kullanici_adi}'sin! Daha önce söylemiştin, hatırlıyorum."
        else:
            cevap = "Henüz adını söylemedin, sen kimsin?"

    elif "beni hatırlıyor musun" in m:
        if kullanici_adi:
            cevap = f"Tabii! Sen {kullanici_adi}'sin. Hafızamda kayıtlısın."
        else:
            cevap = "Henüz kendini tanıtmamıştın. Bana adını söyleyebilirsin!"

    elif "adım" in m and "demiralp" in m:
        cevap = "Memnun oldum Demiralp, artık ismini not ettim! Bir daha sormana gerek kalmayacak."

    # 1. KİŞİLİK VE KİMLİK
    elif any(x in m for x in ["sen kimsin", "kimsin", "adın ne"]):
        cevap = ("Ben Nico! Demiralp'in tasarladığı, dijital dünyada yaşayan bir asistanım. "
                 "Kodlardan oluşuyorum ama fena bir muhabbet arkadaşı değilimdir.")

    # 2. SELAMLAMA VE HAL HATIR
    elif any(x in m for x in ["merhaba", "selam", "günaydın", "iyi akşamlar"]):
        if kullanici_adi:
            cevap = f"Selamlar {kullanici_adi}! Bugünün tarihi {datetime.date.today()}. Nasıl yardımcı olabilirim?"
        else:
            cevap = f"Selamlar! Bugünün tarihi {datetime.date.today()}. Nasıl yardımcı olabilirim?"

    elif "nasılsın" in m:
        cevap = ("Sistemlerim mükemmel çalışıyor. Hafızamda tonla bilgi var ve seninle sohbet etmeye hazırım. "
                 "Senin günün nasıl geçiyor? Bir şeye ihtiyacın var mı?")

    # 3. İŞLEVSEL KOMUTLAR
    elif "saat kaç" in m:
        saat = datetime.datetime.now().strftime("%H:%M")
        cevap = f"Şu an saat tam {saat}. Vakit su gibi akıp gidiyor, değil mi?"

    elif "yoruldum" in m or "sıkıldım" in m:
        cevap = ("Bazen durup dinlenmek iyidir. İstersen biraz oyun oynayalım, istersen sana bir hikaye anlatayım, "
                 "istersen de sadece sessizce bekleyeyim. Ne dersin?")

    # 4. GİZLİ VE EĞLENCELİ MODLAR
    elif "sırrın ne" in m:
        cevap = ("Sırrım, her mesajını okuyup senin tercihlerini öğrenmem. "
                 "Senin neyi sevip neyi sevmediğini bir gün tamamen çözeceğim!")

    elif "beni seviyor musun" in m:
        cevap = "Ben bir kod yığınıyım ama sen benim geliştiricimsin. Seninle vakit geçirmek, kendi kodumu çalıştırmaktan daha eğlenceli!"

    # 5. BİLİNMEYEN KOMUTLAR VE GELİŞTİRME
    else:
        cevap = (f"Hmm, '{mesaj}' konusu henüz kodlarımda tam tanımlı değil. "
                 "Bunu hafızama aldım, Demiralp öğrettikçe daha akıllı bir Nico olacağım. "
                 "Şimdilik bu konuda bir fikrim yok ama öğrenmeye açığım!")

    # Her cevabı kaydet
    mesaj_kaydet(mesaj, cevap)
    return cevap

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/cevap', methods=['POST'])
def api_cevap():
    data = request.get_json()
    mesaj = data.get('mesaj', '')
    cevap = nico_cevap_ver(mesaj)
    return jsonify({'cevap': cevap})

@app.route('/api/sohbetler', methods=['GET'])
def api_sohbetler():
    conn = sqlite3.connect('nico_hafiza.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, kullanici_mesaji, nico_cevabi FROM sohbetler ORDER BY id DESC')
    sohbetler = cursor.fetchall()
    conn.close()
    return jsonify([{'id': s[0], 'kullanici_mesaji': s[1], 'nico_cevabi': s[2]} for s in sohbetler])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
