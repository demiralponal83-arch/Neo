# -*- coding: utf-8 -*-
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

class Base(DeclarativeBase):
    pass

# Initialize Flask app
app = Flask(__name__)
# Replit serves the app through an HTTPS proxy. Trust the proxy headers so
# OAuth providers receive a reachable HTTPS callback URL instead of localhost.
app.wsgi_app = ProxyFix(
    app.wsgi_app,
    x_for=1,
    x_proto=1,
    x_host=1,
    x_port=1,
    x_prefix=1,
)
app.secret_key = os.environ.get("SESSION_SECRET", "nico-secret-key")
app.config["MAINTENANCE_MODE"] = os.environ.get(
    "MAINTENANCE_MODE", "false"
).strip().lower() in {"1", "true", "yes", "on"}
# OAuth starts on the app and returns through Apple's/Replit's top-level
# redirect. Keep the signed state cookie available during that redirect.
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)

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
    # Keep existing Replit Auth databases compatible with the onboarding fields.
    from sqlalchemy import inspect, text
    columns = {column["name"] for column in inspect(db.engine).get_columns("users")}
    with db.engine.begin() as connection:
        if "birth_date" not in columns:
            connection.execute(text("ALTER TABLE users ADD COLUMN birth_date DATE"))
        if "onboarding_completed" not in columns:
            connection.execute(text(
                "ALTER TABLE users ADD COLUMN onboarding_completed BOOLEAN NOT NULL DEFAULT FALSE"
            ))
        if "password_hash" not in columns:
            connection.execute(text("ALTER TABLE users ADD COLUMN password_hash VARCHAR"))
        if "is_suspended" not in columns:
            connection.execute(text(
                "ALTER TABLE users ADD COLUMN is_suspended BOOLEAN NOT NULL DEFAULT FALSE"
            ))
        if "is_closed" not in columns:
            connection.execute(text(
                "ALTER TABLE users ADD COLUMN is_closed BOOLEAN NOT NULL DEFAULT FALSE"
            ))
        if "account_notice" not in columns:
            connection.execute(text("ALTER TABLE users ADD COLUMN account_notice VARCHAR"))
        if "signup_ip_hash" not in columns:
            connection.execute(text("ALTER TABLE users ADD COLUMN signup_ip_hash VARCHAR(128)"))
        if "violation_count" not in columns:
            connection.execute(text(
                "ALTER TABLE users ADD COLUMN violation_count INTEGER NOT NULL DEFAULT 0"
            ))
    logging.info("Database tables created")
