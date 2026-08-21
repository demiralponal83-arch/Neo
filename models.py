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
    birth_date = db.Column(db.Date, nullable=True)
    onboarding_completed = db.Column(db.Boolean, default=False, nullable=False)
    password_hash = db.Column(db.String, nullable=True)
    is_suspended = db.Column(db.Boolean, default=False, nullable=False)
    is_closed = db.Column(db.Boolean, default=False, nullable=False)
    account_notice = db.Column(db.String, nullable=True)
    signup_ip_hash = db.Column(db.String(128), nullable=True, index=True)
    violation_count = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

class MobileToken(db.Model):
    __tablename__ = 'mobile_tokens'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False, index=True)
    token_hash = db.Column(db.String(128), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)

class IPBlacklist(db.Model):
    __tablename__ = 'ip_blacklist'
    id = db.Column(db.Integer, primary_key=True)
    ip_hash = db.Column(db.String(128), unique=True, nullable=False, index=True)
    reason = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)

class SecurityEvent(db.Model):
    __tablename__ = 'security_events'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=True, index=True)
    ip_hash = db.Column(db.String(128), nullable=True, index=True)
    category = db.Column(db.String(40), nullable=False)
    details = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False, index=True)

class AccountAppeal(db.Model):
    __tablename__ = 'account_appeals'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False, index=True)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String, nullable=False, default='Yeni')
    created_at = db.Column(db.DateTime, default=datetime.now, index=True)
    user = db.relationship('User', backref=db.backref('account_appeals', lazy=True))

class AppSetting(db.Model):
    __tablename__ = 'app_settings'
    key = db.Column(db.String, primary_key=True)
    value = db.Column(db.String, nullable=False)

class VisitorVisit(db.Model):
    __tablename__ = 'visitor_visits'
    id = db.Column(db.Integer, primary_key=True)
    visitor_key = db.Column(db.String, nullable=False, index=True)
    path = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now, index=True)

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
