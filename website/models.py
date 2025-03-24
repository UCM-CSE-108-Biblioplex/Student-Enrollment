from flask_login import UserMixin
from . import db
import time # useful later for potential API Keys

class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    is_admin = db.Column(db.Boolean, default=False)
    username = db.Column(db.String(255), unique=True, nullable=False)
    email = db.Column(db.String(255))
    password = db.Column(db.String(255), nullable=False, info={"min_length": 4})

class APIKey(db.Model):
    __tablename__ = "keys"
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(255), nullable=False)
    expiry = db.Column(db.Integer, nullable=False)