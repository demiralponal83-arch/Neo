---
name: Neo bağlantı uyarısı
description: Cevap servisi kullanılamadığında kullanıcıya gösterilen hata davranışı
---

Cevap servisi başarısız olduğunda API sohbet cevabı döndürmez; arayüz, servis adı veya teknik ayrıntı içermeyen turuncu bir uyarı gösterir: “Şu anda yanıt veremiyorum. Lütfen biraz sonra tekrar dene.” Servis çağrısında kota hatalarında gereksiz tekrar yapılmaz; çalışan hafif model ilk sırada, geçici ağ/model hatalarında sınırlı alternatif model sırası kullanılır.

**Why:** Kullanıcı teknik servis adının veya bağlantı hatasının sohbet balonunda görünmesini istemedi; ayrıca kota sınırındaki modelleri tekrar tekrar çağırmak yanıt oranını düşürüyordu.

**How to apply:** Geçici cevap hatalarında aynı sessiz API + arayüz uyarısı yaklaşımını koru; kullanıcıya görünen metinde sağlayıcı adı kullanma.