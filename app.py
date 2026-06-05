import streamlit as st
from main import nico_cevap_ver

st.title("Nico - Kişisel Asistan")

# Sohbet geçmişini gösterme (Hafızadan çekmek için)
if "mesajlar" not in st.session_state:
    st.session_state.mesajlar = []

# Mesajları ekrana yazdır
for mesaj in st.session_state.mesajlar:
    with st.chat_message(mesaj["rol"]):
        st.markdown(mesaj["icerik"])

# Kullanıcıdan mesaj al
if prompt := st.chat_input("Nico'ya bir şeyler yaz..."):
    # Kullanıcının mesajını ekrana ekle
    st.session_state.mesajlar.append({"rol": "user", "icerik": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Nico'nun cevabını al
    cevap = nico_cevap_ver(prompt)

    # Nico'nun cevabını ekrana ekle
    st.session_state.mesajlar.append({"rol": "assistant", "icerik": cevap})
    with st.chat_message("assistant"):
        st.markdown(cevap)
