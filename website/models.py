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
    api_keys = db.relationship("APIKey", backref="user")
    courses = db.relationship("Course", secondary="roles", back_populates="users")

class Course(db.Model):
    __tablename__ = "courses"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    dept = db.Column(db.String(10), nullable=False)
    number = db.Column(db.Integer, nullable=False)
    users = db.relationship(
        "User", secondary="roles", back_populates="courses"
    )

class Role(db.Model):
    __tablename__ = "roles"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(63, nullable=False))

roles = db.Table(
    "roles",
    db.Column("user_id", db.Integer, db.ForeignKey("users.id"), primary_key=True),
    db.Column("course_id", db.Integer, db.ForeignKey("courses.id"), primary_key=True),
    db.Column("role_id", db.Integer, db.ForeignKey("roles.id"))
)

class APIKey(db.Model):
    __tablename__ = "keys"
    id = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.Integer, db.ForeignKey("users.id"))
    key = db.Column(db.String(255), nullable=False)
    expiry = db.Column(db.Integer, nullable=False)