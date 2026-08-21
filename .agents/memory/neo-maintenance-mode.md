---
name: Neo bakım ekranı
description: Geliştirme sırasında ziyaretçilere gösterilen bakım görünümü
---

Neo’nun arayüzü geliştirilirken ziyaretçilerin yarım veya bozuk ekran görmemesi için bakım görünümü kullanılabilir. Bakım modu ortam değişkeniyle açılır; varsayılan olarak kapalıdır ve normal site akışı değişmez.

**Why:** Kullanıcı, site üzerinde düzenleme yapılırken estetik ve temaya uygun bir “Neo geliştiriliyor” ekranı istedi.

**How to apply:** Büyük arayüz değişikliklerinden önce `MAINTENANCE_MODE=true` kullan; çalışma bittiğinde bayrağı kapatıp normal giriş ve sohbet akışını geri aç.