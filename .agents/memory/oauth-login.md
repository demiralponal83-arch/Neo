---
name: OAuth giriş dayanıklılığı
description: Replit OAuth sağlayıcıları ve callback hata davranışı için kalıcı uygulama kuralı
---

Replit Auth sağlayıcıları (Apple dahil) aynı OAuth akışını kullanır; uygulama tarafında giriş bağlantısı blueprint’in gerçek login endpoint’inden üretilmeli, callback state/PKCE değerlerini taşıyan session cookie HTTPS proxy arkasında `Secure` ve `SameSite=Lax` olmalıdır, sağlayıcı/callback hataları da mevcut bir hata şablonuna yönlenmelidir.

**Why:** Sağlayıcı seçimi dış kimlik sağlayıcısında yapılır; uygulamadaki yanlış veya sabitlenmiş rota 404 ya da boş hata ekranı oluşturabilir.

**How to apply:** Auth rotalarını `url_for` ile üret, callback hata rotasını gerçek bir şablona bağla ve OAuth giriş/çıkış yönlendirmelerini workflow testleriyle kontrol et.