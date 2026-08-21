---
name: Neo bağlam tabanlı cevap
description: Neo’nun mesajları sabit niyet kategorileri yerine doğrudan bağlamla yanıtlaması
---

Neo’nun ana cevap akışı mesajları intent, tarif, bilgi veya öğrenilmiş cevap kategorilerine eşleştirmez. Kullanıcı mesajı ve kısa konuşma geçmişi doğrudan doğal dil modeline gönderilir; model kullanılamazsa nötr bir fallback kullanılır.

**Why:** Anahtar kelime ve öğrenilmiş niyet eşleştirmeleri “napıyosun?” gibi günlük cümleleri yanlışlıkla tarif veya başka bir konuya çevirebiliyordu.

**How to apply:** Yeni cevap özelliklerini sabit intent dalları ekleyerek değil, bağlam istemini ve fallback davranışını geliştirerek ekle.