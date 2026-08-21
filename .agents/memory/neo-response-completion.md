---
name: Neo yanıt tamamlama
description: Gemini yanıtlarının kullanıcıya yarım cümle olarak gösterilmesini önleyen davranış
---

Neo’nun model yanıtları yalnızca ilk metin parçası okunarak gösterilmemeli. Gemini `finishReason` değerini bildirdiğinde veya uzun yanıt noktalama olmadan bittiğinde, eksik devam ayrı bir istekle alınarak ilk parçaya eklenir.

**Why:** Model bazı yanıtları çıktı sınırında veya tamamlanmamış cümlede kesebiliyor; kullanıcı yarım cevap görüyor.

**How to apply:** Gemini yanıt işleme kodunda `finishReason` kontrolünü ve tamamlanmamış uzun metin için devam istemini koru; tüm `content.parts` parçalarını birleştir.