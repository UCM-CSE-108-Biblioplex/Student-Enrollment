from flask_login import UserMixin
from . import db
import time  # useful later for potential API Keys

class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    is_admin = db.Column(db.Boolean, default=False)
    first_name = db.Column(db.String(255), nullable=False)
    middle_name = db.Column(db.String(255), nullable=True)
    last_name = db.Column(db.String(255), nullable=True)
    username = db.Column(db.String(255), unique=True, nullable=False, info={"min_length": 2})
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False, info={"min_length": 4})
    api_keys = db.relationship("APIKey", backref="user")
    courses = db.relationship(
        "Course", secondary="roles", back_populates="users"
    )

    def to_dict(self):
        return({attr.name: getattr(self, attr.name) for attr in self.__table__.columns})

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
    __tablename__ = "roles_def"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(63), nullable=False)

roles = db.Table(
    "roles",
    db.metadata,
    db.Column("user_id", db.Integer, db.ForeignKey("users.id"), primary_key=True),
    db.Column("course_id", db.Integer, db.ForeignKey("courses.id"), primary_key=True),
    db.Column("role_id", db.Integer, db.ForeignKey("roles_def.id"))
)

class APIKey(db.Model):
    __tablename__ = "keys"
    id = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.Integer, db.ForeignKey("users.id"))
    is_admin = db.Column(db.Boolean, default=False)
    key = db.Column(db.String(255), nullable=False)
    expiry = db.Column(db.Integer, nullable=False)
