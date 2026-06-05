import sqlite3

def mesaj_kaydet(kullanici_mesaji, nico_cevabi):
    conn = sqlite3.connect('nico_hafiza.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO sohbetler (kullanici_mesaji, nico_cevabi) VALUES (?, ?)', 
                   (kullanici_mesaji, nico_cevabi))
    conn.commit()
    conn.close()

def nico_cevap_ver(mesaj):
    # Hafızada geçmiş mesajları ara
    conn = sqlite3.connect('nico_hafiza.db')
    cursor = conn.cursor()
    cursor.execute('SELECT kullanici_mesaji, nico_cevabi FROM sohbetler')
    gecmis = cursor.fetchall()
    conn.close()

    # Kullanıcı daha önce adını söylemiş mi?
    for k_mesaj, n_cevap in gecmis:
        if "adım" in k_mesaj.lower() and "demiralp" in k_mesaj.lower():
            if "adım ne" in mesaj.lower() or "ben kimim" in mesaj.lower():
                return "Sen Demiralp'sin! Daha önce söylemiştin, hatırladım."
            if "merhaba" in mesaj.lower():
                return "Selam Demiralp! Seni hatırlıyorum."

    # Yeni mesajları işle
    if "adım" in mesaj.lower() and "demiralp" in mesaj.lower():
        cevap = "Memnun oldum Demiralp, artık ismini not ettim!"
    elif "adım ne" in mesaj.lower() or "ben kimim" in mesaj.lower():
        cevap = "Henüz adını söylemedin, sen kimsin?"
    elif "merhaba" in mesaj.lower():
        cevap = "Selam! Ben Nico, senin kişisel asistanınım."
    elif "nasılsın" in mesaj.lower():
        cevap = "Süperim! Kodlarım tıkır tıkır çalışıyor, ya sen?"
    else:
        cevap = f"Not ettim: {mesaj}"

    # Sohbeti hafızaya kaydet
    mesaj_kaydet(mesaj, cevap)
    return cevap
