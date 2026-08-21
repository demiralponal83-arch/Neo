---
name: Neo iOS uygulaması
description: Neo’nun Expo tabanlı mobil istemcisi ve backend bağlantısı
---

Neo’nun mobil istemcisi Expo/React Native ile ayrı bir uygulama olarak tutulur ve mevcut Flask backend’ine Bearer token tabanlı mobil API üzerinden bağlanır. İlk mobil kapsam e-posta/şifre girişi, kayıt, profil başlangıcı, sohbet, geçmiş, yeni sohbet ve çıkıştır. Backend adresi uygulamaya sabit yazılmaz; `EXPO_PUBLIC_API_BASE_URL` ile verilir.

Yönetim paneli de ayrı bir PWA manifestiyle `/yonetim` adresinden ana ekrana eklenebilir; adı “Neo Yönetim”, ikonu ortak Neo logosudur.

**Why:** Mevcut web uygulamasını bozmadan Neo’yu iPhone’da gerçek uygulama olarak test edip daha sonra App Store’a gönderebilmek için.

**How to apply:** Önce backend’i herkese açık HTTPS adresinde yayınla, mobil `.env` adresini buna bağla, sonra Expo EAS ile iOS build al. App Store’a gönderilecek uygulamada bundle ID ve mağaza görsellerini sonlandır.