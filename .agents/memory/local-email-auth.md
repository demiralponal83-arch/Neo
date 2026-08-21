---
name: Yerel e-posta girişi
description: Nico'nun Replit üyeliği olmadan kullandığı yerel hesap giriş sistemi
---

Nico artık kendi e-posta ve şifre hesaplarını kabul eder. Şifreler düz metin tutulmaz; hash olarak saklanır. Yerel hesaplar Flask-Login oturumuyla çalışır ve Replit OAuth token kontrolüne ihtiyaç duymaz. Kayıt sonrası mevcut yaş/ad-soyad onboarding’i açılır.

**Why:** Kullanıcı Replit üyeliği istemedi ve Nico’ya doğrudan e-posta/şifre ile kayıt olmak istedi.

**How to apply:** Yerel hesaplarda kimlik doğrulama için e-posta + hash doğrulaması kullan; OAuth akışını yerel hesaplara zorunlu kılma. E-posta doğrulaması istenirse gerçek bir mail sağlayıcısı bağlanmadan sahte kod akışı kurma.