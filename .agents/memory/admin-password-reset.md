---
name: Yönetici şifre sıfırlama
description: Yönetim panelinden kullanıcıların yerel giriş şifrelerini değiştirme
---

Yönetim panelindeki her kullanıcı satırında “Şifre değiştir” alanı bulunur. Yönetici en az 8 karakterlik yeni şifre belirlediğinde şifre hash’lenerek kaydedilir; düz metin şifre panelde veya loglarda tutulmaz.

**Why:** Kullanıcılar şifrelerini unuttuğunda yönetici hesabın erişimini geri kazandırabilmeli.

**How to apply:** Yeni yönetici şifre işlemlerinde aynı hash tabanlı yerel giriş yöntemini koru; minimum uzunluk kontrolünü sunucu tarafında zorunlu tut.