---
name: Yönetici test hesabı
description: Yönetici panelinden gerçek kullanıcılara dokunmadan Neo’yu test etme
---

Yönetim panelindeki “Test hesabıyla Neo’yu aç” düğmesi izole bir test hesabını ilk kullanımda oluşturur ve yönetici oturumunu bu hesaba geçirir. Neo ekranında sağ altta askıya alma, tamamen kapatma, geri açma, şifre değiştirme ve testten çıkma araçları bulunur. Araçlar yalnızca yönetim paneliyle açılmış test oturumunda çalışır.

**Why:** Yönetici gerçek kullanıcı hesaplarını değiştirmeden askıya alma, kapatma, açılma ve şifre akışlarını normal kullanıcı gibi deneyebilmek istedi.

**How to apply:** Test hesabını üretim kullanıcılarından ayrı tut; test araçlarının endpoint’lerinde yönetim paneli oturumu ve test modu kontrollerini koru. Test ekranı düğmeleri gerçek POST formu göndermeli; yönetim paneli düğmeleri işlem sonrası tam sayfa yenilemelidir. Sunucu işlem sonrası doğru durum ekranına yönlendirmeli ve durum ekranları önbelleğe alınmamalı.