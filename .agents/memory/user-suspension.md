---
name: Kullanıcı hesap askıya alma
description: Yönetici panelinden kullanıcı hesaplarını geçici olarak kapatma ve geri açma
---

Yönetici panelindeki kullanıcı hesapları bölümünden belirli bir hesap askıya alınabilir veya geri açılabilir. Askıya alınan kullanıcı mevcut oturumda ve sonraki girişte “Hesabımız askıya alındı (isim)” ekranını görür; yalnızca güvenli çıkış yapabilir.

**Why:** Kullanıcı, istediği hesapların erişimini yönetim panelinden kontrol etmek ve askıya alınan kişiye açık bir durum ekranı göstermek istedi.

**How to apply:** Hesap erişimiyle ilgili yeni kontrollerde `is_suspended` durumunu kullan; askıya alınmış hesapların çıkış ve yönetici akışlarını engelleme.