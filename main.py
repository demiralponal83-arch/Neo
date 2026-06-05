import sqlite3

def mesaj_kaydet(kullanici_mesaji, nico_cevabi):
    conn = sqlite3.connect('nico_hafiza.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO sohbetler (kullanici_mesaji, nico_cevabi) VALUES (?, ?)', 
                   (kullanici_mesaji, nico_cevabi))
    conn.commit()
    conn.close()

def def nico_cevap_ver(mesaj):
    # Basit bir hafıza mantığı
    if "adım" in mesaj.lower() and "demiralp" in mesaj.lower():
        cevap = "Memnun oldum Demiralp, artık ismini not ettim!"
    elif "adım ne" in mesaj.lower() or "ben kimim" in mesaj.lower():
        cevap = "Sen benim geliştiricim Demiralp'sin!"
    elif "merhaba" in mesaj.lower():
        cevap = "Selam Demiralp, hoş geldin!"
    else:
        cevap = f"Not ettim: {mesaj}"

    # Sohbeti hafızaya al
    mesaj_kaydet(mesaj, cevap)
    return cevap

    # BURASI NICO'NUN KENDİ MANTIĞI:
    # İleride buraya kendi kurallarını veya yapay zeka modelini ekleyebilirsin.

    if "merhaba" in mesaj.lower():
        cevap = "Selam! Ben Nico, senin kişisel asistanınım."
    elif "nasılsın" in mesaj.lower():
        cevap = "Süperim! Kodlarım tıkır tıkır çalışıyor, ya sen?"
    else:
        cevap = f"Şu an bunu düşünecek kadar gelişmedim ama şunu not ettim: {mesaj}"

    # Sohbeti hafızaya al
    mesaj_kaydet(mesaj, cevap)
    return cevap
