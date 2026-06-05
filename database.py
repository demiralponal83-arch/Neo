import sqlite3

def init_db():
    conn = sqlite3.connect('nico_hafiza.db')
    cursor = conn.cursor()
    # Sohbetleri tutacak tabloyu oluşturuyoruz
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sohbetler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kullanici_mesaji TEXT,
            nico_cevabi TEXT
        )
    ''')
    conn.commit()
    conn.close()

# İlk çalıştırmada tabloyu oluşturması için bunu çağıracağız
if __name__ == "__main__":
    init_db()
    print("Nico'nun hafızası başarıyla oluşturuldu!")
