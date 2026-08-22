# -*- coding: utf-8 -*-
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "nico-secret-key")

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

# 1. Ortam Değişkenlerini (Environment Variables) Güvenli Şekilde Oku
# Eğer sistemde veya Streamlit Secrets'ta değer yoksa varsayılan SQLite veritabanını kullanır
database_uri = os.environ.get('SQLALCHEMY_DATABASE_URI')

if not database_uri:
    try:
        import streamlit as st
        database_uri = st.secrets.get("SQLALCHEMY_DATABASE_URI")
    except Exception:
        pass

# Hiçbir yerde tanımlı değilse çökmemesi için otomatik SQLite adresi atar
if not database_uri:
    database_uri = 'sqlite:///database.db'

# 2. Flask Uygulamasını Oluştur ve Yapılandır
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = database_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SESSION_SECRET', 'varsayilan-gizli-anahtar')

# 3. Veritabanı Sınıfı Tanımı ve Başlatma
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(app, model_class=Base)

# Kendi model ve route (sayfa) kodların bundan sonra aynen devam edebilir...

}

# Initialize SQLAlchemy
db = SQLAlchemy(app, model_class=Base)

# Create tables
with app.app_context():
    import models  # noqa: F401
    db.create_all()
    logging.info("Database tables created")
