# -*- coding: utf-8 -*-
from datetime import datetime
from app import db
from flask_dance.consumer.storage.sqla import OAuthConsumerMixin
from flask_login import UserMixin
from sqlalchemy import UniqueConstraint

# ============================================================
# REPLIT AUTH - ZORUNLU TABLOLAR
# ============================================================
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.String, primary_key=True)
    email = db.Column(db.String, unique=True, nullable=True)
    first_name = db.Column(db.String, nullable=True)
    last_name = db.Column(db.String, nullable=True)
    profile_image_url = db.Column(db.String, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

class OAuth(OAuthConsumerMixin, db.Model):
    user_id = db.Column(db.String, db.ForeignKey(User.id))
    browser_session_key = db.Column(db.String, nullable=False)
    user = db.relationship(User)

    __table_args__ = (UniqueConstraint(
        'user_id', 'browser_session_key', 'provider',
        name='uq_user_browser_session_key_provider',
    ),)

# ============================================================
# NICO AI TABLOLARI
# ============================================================
class Sohbetler(db.Model):
    __tablename__ = 'sohbetler'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    konu = db.Column(db.String, nullable=False)
    zaman = db.Column(db.DateTime, default=datetime.now)

class Mesajlar(db.Model):
    __tablename__ = 'mesajlar'
    id = db.Column(db.Integer, primary_key=True)
    sohbet_id = db.Column(db.Integer, db.ForeignKey('sohbetler.id'), nullable=False)
    gonderen = db.Column(db.String, nullable=False)
    mesaj = db.Column(db.Text, nullable=False)
    zaman = db.Column(db.DateTime, default=datetime.now)

class AI_Egitim(db.Model):
    __tablename__ = 'ai_egitim'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    mesaj = db.Column(db.Text, nullable=False)
    intent = db.Column(db.String, nullable=False)
    cevap = db.Column(db.Text, nullable=False)
    zaman = db.Column(db.DateTime, default=datetime.now)

class AI_Bilgi(db.Model):
    __tablename__ = 'ai_bilgi'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    konu = db.Column(db.String, nullable=False)
    bilgi = db.Column(db.Text, nullable=False)
    zaman = db.Column(db.DateTime, default=datetime.now)
