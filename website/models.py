from flask_login import UserMixin
from . import db
import time # useful later for potential API Keys

class User(db.Model, UserMixin):
    __tablename__ = "user"
    id = db.Column(db.String(32), primary_key=True)
    is_admin = db.Column(db.Boolean, default=False)
    username = db.Column(db.String(255), unique=True, nullable=False)
    email = db.Column(db.String(255))
    password = db.Column(db.String(255), nullable=False, info={"min_length": 4})