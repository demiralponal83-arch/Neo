# Neo iPhone uygulaması

Bu klasör, mevcut Neo Flask backend'ine bağlanan Expo uygulamasıdır.

## Yerel geliştirme

1. `mobile/.env.example` dosyasını `.env` olarak kopyala.
2. `EXPO_PUBLIC_API_BASE_URL` değerini Neo'nun herkese açık HTTPS adresiyle değiştir.
3. `cd mobile && npm install`
4. `npx expo start`
5. iPhone'da Expo Go ile QR kodu aç.

Uygulama e-posta/şifre girişi, kayıt, profil başlangıcı, sohbet, sohbet geçmişi ve çıkış akışlarını kullanır. App Store gönderimi için `app.json` içindeki iOS bundle kimliği ve uygulama mağazası görselleri ayrıca sonlandırılmalıdır.