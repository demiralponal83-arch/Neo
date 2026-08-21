import React, { useEffect, useMemo, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  FlatList,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  SafeAreaView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { StatusBar } from "expo-status-bar";

const API_BASE_URL = process.env.EXPO_PUBLIC_API_BASE_URL || "https://YOUR-NEO-DEPLOYMENT.replit.app";
const TOKEN_KEY = "neo_mobile_token";
const colors = {
  ink: "#26384C",
  muted: "#7B8796",
  line: "#DDE3E8",
  canvas: "#F4F6F8",
  card: "#FFFFFF",
  accent: "#34465B",
};

async function api(path, options = {}, token) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {}),
    },
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.error || "Bir şeyler ters gitti.");
  return body;
}

function Logo({ small = false }) {
  return (
    <View style={[styles.logo, small && styles.smallLogo]}>
      <Text style={[styles.logoText, small && styles.smallLogoText]}>N</Text>
    </View>
  );
}

function AuthScreen({ onLogin }) {
  const [register, setRegister] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function submit() {
    setError("");
    setBusy(true);
    try {
      const result = await api(register ? "/api/mobile/kayit" : "/api/mobile/giris", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      await AsyncStorage.setItem(TOKEN_KEY, result.token);
      onLogin(result.token, result.user);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <SafeAreaView style={styles.safe}>
      <StatusBar style="dark" />
      <View style={styles.authWrap}>
        <Logo />
        <Text style={styles.title}>Neo&apos;ya hoş geldin</Text>
        <Text style={styles.subtitle}>Sana iyi gelen, sade ve doğal bir asistan.</Text>
        <TextInput style={styles.input} placeholder="E-posta" autoCapitalize="none" keyboardType="email-address" value={email} onChangeText={setEmail} />
        <TextInput style={styles.input} placeholder="Şifre" secureTextEntry value={password} onChangeText={setPassword} />
        {!!error && <Text style={styles.error}>{error}</Text>}
        <Pressable style={styles.primaryButton} onPress={submit} disabled={busy}>
          {busy ? <ActivityIndicator color="#FFF" /> : <Text style={styles.primaryText}>{register ? "Hesap oluştur" : "Giriş yap"}</Text>}
        </Pressable>
        <Pressable onPress={() => { setRegister(!register); setError(""); }}>
          <Text style={styles.switchText}>{register ? "Zaten hesabın var mı? Giriş yap" : "Hesabın yok mu? Hesap oluştur"}</Text>
        </Pressable>
      </View>
    </SafeAreaView>
  );
}

function Onboarding({ token, onComplete }) {
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [birthDate, setBirthDate] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function submit() {
    setBusy(true); setError("");
    try {
      const user = await api("/api/mobile/profil", {
        method: "PATCH",
        body: JSON.stringify({ first_name: firstName, last_name: lastName, birth_date: birthDate }),
      }, token);
      onComplete(user);
    } catch (e) { setError(e.message); } finally { setBusy(false); }
  }
  return (
    <SafeAreaView style={styles.safe}><View style={styles.authWrap}>
      <Logo small /><Text style={styles.title}>Önce seni tanıyalım</Text>
      <Text style={styles.subtitle}>Neo&apos;yu kullanmak için bilgilerini tamamla.</Text>
      <TextInput style={styles.input} placeholder="Ad" value={firstName} onChangeText={setFirstName} />
      <TextInput style={styles.input} placeholder="Soyad" value={lastName} onChangeText={setLastName} />
      <TextInput style={styles.input} placeholder="Doğum tarihi (YYYY-AA-GG)" value={birthDate} onChangeText={setBirthDate} />
      {!!error && <Text style={styles.error}>{error}</Text>}
      <Pressable style={styles.primaryButton} onPress={submit} disabled={busy}>{busy ? <ActivityIndicator color="#FFF" /> : <Text style={styles.primaryText}>Devam et</Text>}</Pressable>
    </View></SafeAreaView>
  );
}

function ChatScreen({ token, user, onLogout }) {
  const [messages, setMessages] = useState([]);
  const [history, setHistory] = useState([]);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [showHistory, setShowHistory] = useState(false);

  async function loadHistory() {
    try { setHistory(await api("/api/mobile/sohbetler", {}, token)); } catch (e) { Alert.alert("Neo", e.message); }
  }
  useEffect(() => { loadHistory(); }, []);
  async function send() {
    const message = text.trim();
    if (!message || busy) return;
    setText(""); setMessages((current) => [...current, { gonderen: "kullanici", mesaj: message }]); setBusy(true);
    try {
      const result = await api("/api/mobile/cevap", { method: "POST", body: JSON.stringify({ mesaj: message }) }, token);
      setMessages((current) => [...current, { gonderen: "nico", mesaj: result.cevap }]);
      loadHistory();
    } catch (e) { Alert.alert("Neo", e.message); } finally { setBusy(false); }
  }
  async function openChat(id) {
    try { setMessages(await api(`/api/mobile/sohbet/${id}`, {}, token)); setShowHistory(false); }
    catch (e) { Alert.alert("Neo", e.message); }
  }
  return (
    <SafeAreaView style={styles.safe}>
      <KeyboardAvoidingView style={styles.flex} behavior={Platform.OS === "ios" ? "padding" : undefined}>
        <View style={styles.header}><Pressable onPress={() => setShowHistory(!showHistory)}><Text style={styles.headerAction}>☰</Text></Pressable><View style={styles.headerBrand}><Logo small /><Text style={styles.headerTitle}>Neo</Text></View><Pressable onPress={() => Alert.alert("Hesap", `${user.isim || "Neo kullanıcısı"}\n${user.email}`, [{ text: "Çıkış yap", style: "destructive", onPress: onLogout }, { text: "Vazgeç" }])}><Text style={styles.headerAction}>◉</Text></Pressable></View>
        {showHistory && <View style={styles.drawer}><Text style={styles.drawerTitle}>Sohbet geçmişi</Text><Pressable style={styles.newChat} onPress={() => { setMessages([]); setShowHistory(false); }}><Text style={styles.newChatText}>＋ Yeni sohbet</Text></Pressable><FlatList data={history} keyExtractor={(item) => String(item.id)} renderItem={({ item }) => <Pressable style={styles.historyItem} onPress={() => openChat(item.id)}><Text style={styles.historyTitle} numberOfLines={1}>{item.konu || "Yeni sohbet"}</Text><Text style={styles.historyTime}>{item.zaman}</Text></Pressable>} ListEmptyComponent={<Text style={styles.empty}>Henüz sohbet yok.</Text>} /></View>}
        <FlatList style={styles.messages} contentContainerStyle={styles.messageContent} data={messages} keyExtractor={(_, index) => String(index)} renderItem={({ item }) => <View style={[styles.bubble, item.gonderen === "kullanici" ? styles.userBubble : styles.neoBubble]}><Text style={item.gonderen === "kullanici" ? styles.userText : styles.neoText}>{item.mesaj}</Text></View>} ListEmptyComponent={<View style={styles.welcome}><Logo /><Text style={styles.welcomeTitle}>Bugün ne hakkında konuşalım?</Text><Text style={styles.welcomeText}>Neo burada.</Text></View>} />
        <View style={styles.composer}><TextInput style={styles.composerInput} placeholder="Neo&apos;ya bir şey yaz..." value={text} onChangeText={setText} multiline /><Pressable style={styles.send} onPress={send}><Text style={styles.sendText}>↑</Text></Pressable></View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

export default function App() {
  const [token, setToken] = useState(null);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    AsyncStorage.getItem(TOKEN_KEY).then(async (saved) => {
      if (!saved) return;
      try { setToken(saved); setUser(await api("/api/mobile/kullanici", {}, saved)); }
      catch { await AsyncStorage.removeItem(TOKEN_KEY); }
      finally { setLoading(false); }
    }).finally(() => setLoading(false));
  }, []);
  if (loading) return <SafeAreaView style={styles.safe}><ActivityIndicator style={styles.loader} color={colors.accent} /></SafeAreaView>;
  if (!token || !user) return <AuthScreen onLogin={(newToken, newUser) => { setToken(newToken); setUser(newUser); }} />;
  if (!user.profil_tamam) return <Onboarding token={token} onComplete={setUser} />;
  return <ChatScreen token={token} user={user} onLogout={async () => { await api("/api/mobile/cikis", { method: "POST" }, token).catch(() => {}); await AsyncStorage.removeItem(TOKEN_KEY); setToken(null); setUser(null); }} />;
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.canvas },
  flex: { flex: 1 },
  loader: { flex: 1 },
  authWrap: { flex: 1, justifyContent: "center", padding: 28 },
  logo: { width: 72, height: 72, borderRadius: 23, backgroundColor: colors.accent, alignItems: "center", justifyContent: "center", alignSelf: "center", marginBottom: 20 },
  smallLogo: { width: 32, height: 32, borderRadius: 10, marginBottom: 0 },
  logoText: { color: "#FFF", fontSize: 38, fontWeight: "800" },
  smallLogoText: { fontSize: 18 },
  title: { color: colors.ink, fontSize: 27, fontWeight: "800", textAlign: "center", letterSpacing: -0.8 },
  subtitle: { color: colors.muted, textAlign: "center", lineHeight: 21, marginTop: 10, marginBottom: 28 },
  input: { height: 52, borderWidth: 1, borderColor: colors.line, borderRadius: 13, backgroundColor: colors.card, paddingHorizontal: 15, marginBottom: 12, color: colors.ink },
  primaryButton: { height: 52, borderRadius: 13, alignItems: "center", justifyContent: "center", backgroundColor: colors.accent, marginTop: 6 },
  primaryText: { color: "#FFF", fontWeight: "800", fontSize: 15 },
  switchText: { color: colors.accent, textAlign: "center", marginTop: 20, fontWeight: "700", fontSize: 13 },
  error: { color: "#A84A5D", backgroundColor: "#FFF0F3", padding: 11, borderRadius: 10, marginBottom: 8, fontSize: 13 },
  header: { height: 64, paddingHorizontal: 18, flexDirection: "row", alignItems: "center", justifyContent: "space-between", borderBottomWidth: 1, borderBottomColor: colors.line, backgroundColor: colors.card },
  headerBrand: { flexDirection: "row", alignItems: "center", gap: 8 },
  headerTitle: { color: colors.ink, fontSize: 18, fontWeight: "800" },
  headerAction: { color: colors.ink, fontSize: 22 },
  drawer: { position: "absolute", zIndex: 5, top: 64, left: 0, bottom: 0, width: "82%", padding: 18, backgroundColor: colors.card, borderRightWidth: 1, borderRightColor: colors.line, shadowColor: "#000", shadowOpacity: 0.12, shadowRadius: 20, elevation: 8 },
  drawerTitle: { color: colors.ink, fontSize: 18, fontWeight: "800", marginBottom: 14 },
  newChat: { padding: 13, borderRadius: 11, backgroundColor: colors.canvas, marginBottom: 14 },
  newChatText: { color: colors.accent, fontWeight: "800" },
  historyItem: { paddingVertical: 13, borderBottomWidth: 1, borderBottomColor: colors.line },
  historyTitle: { color: colors.ink, fontWeight: "700" },
  historyTime: { color: colors.muted, fontSize: 11, marginTop: 4 },
  empty: { color: colors.muted, textAlign: "center", marginTop: 20 },
  messages: { flex: 1 },
  messageContent: { padding: 18, flexGrow: 1, justifyContent: "flex-end", gap: 10 },
  bubble: { maxWidth: "84%", padding: 13, borderRadius: 17 },
  userBubble: { alignSelf: "flex-end", backgroundColor: colors.accent, borderBottomRightRadius: 5 },
  neoBubble: { alignSelf: "flex-start", backgroundColor: colors.card, borderWidth: 1, borderColor: colors.line, borderBottomLeftRadius: 5 },
  userText: { color: "#FFF", lineHeight: 20 },
  neoText: { color: colors.ink, lineHeight: 20 },
  welcome: { alignItems: "center", marginBottom: 28 },
  welcomeTitle: { color: colors.ink, fontSize: 19, fontWeight: "800", marginTop: 2 },
  welcomeText: { color: colors.muted, marginTop: 6 },
  composer: { flexDirection: "row", alignItems: "flex-end", gap: 8, padding: 12, borderTopWidth: 1, borderTopColor: colors.line, backgroundColor: colors.card },
  composerInput: { flex: 1, maxHeight: 110, minHeight: 46, paddingHorizontal: 14, paddingVertical: 12, borderRadius: 14, backgroundColor: colors.canvas, color: colors.ink },
  send: { width: 46, height: 46, borderRadius: 14, backgroundColor: colors.accent, alignItems: "center", justifyContent: "center" },
  sendText: { color: "#FFF", fontSize: 25, fontWeight: "700", marginTop: -3 },
});