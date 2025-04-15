from werkzeug.security import generate_password_hash as gph
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from dotenv import load_dotenv
from flask import Flask
import os

load_dotenv()

db = SQLAlchemy()

FLASK_SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", None)
if(FLASK_SECRET_KEY is None):
    print("WARNING: Secret key was not set; using default value.")
    FLASK_SECRET_KEY = "somesecretkey"
DB_NAME = os.environ.get("DB_NAME", "database.db")

def start():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = FLASK_SECRET_KEY
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_NAME}"

    db.init_app(app)

    from .api_main import api_main

    from .site_auth import site_auth
    from .site_enrollment import site_enrollment
    from .site_main import site_main
    from .site_admin import site_admin

    app.register_blueprint(api_main, url_prefix="/api/v1")

    app.register_blueprint(site_auth, url_prefix="/auth")
    app.register_blueprint(site_enrollment, url_prefix="/enrollment")
    app.register_blueprint(site_main, url_prefix="/")
    app.register_blueprint(site_admin, url_prefix="/admin")

    from .models import User, Role

    login_manager = LoginManager()
    login_manager.login_view = "site_auth.login"
    login_manager.init_app(app)

    create_database(app)

    with app.app_context():
        app.config["student_role"] = Role.query.filter_by(name="Student").first()
        app.config["instructor_role"] = Role.query.filter_by(name="Instructor").first()
        app.config["ta_role"] = Role.query.filter_by(name="TA").first()
        app.config["admin_role"] = Role.query.filter_by(name="Admin").first()

    @login_manager.user_loader
    def load_user(id):
        return(User.query.get(id))

    return(app)

def create_database(app):
    if(os.path.exists(os.path.join("./instance/", DB_NAME))):
        return
    
    with app.app_context():
        db.create_all()

        from .models import Role, User

        # student, instructor, admin roles
        student_role = Role(name="Student")
        db.session.add(student_role)
        instructor_role = Role(name="Instructor")
        db.session.add(instructor_role)
        ta_role = Role(name="TA")
        db.session.add(ta_role)

        # user-defined roles
        # in case of unforeseen use cases (e.g., Learning Assistent, etc.)
        defined_roles = os.getenv("EXTRA_ROLES", None)
        if(defined_roles):
            defined_roles = defined_roles.split(",")
            for role in defined_roles:
                new_role = Role(name=role)
                db.session.add(new_roll)

        admin_user = User(
            first_name=os.environ.get("DEFAULT_ADMIN_FIRST_NAME", "admin"),
            last_name=os.environ.get("DEFAULT_ADMIN_LAST_NAME", "admin"),
            username=os.environ.get("DEFAULT_ADMIN_USERNAME", "admin"),
            email=os.environ.get("DEFAULT_ADMIN_EMAIL", "admin@example.com"),
            password=gph(
                os.environ.get("DEFAULT_ADMIN_PASSWORD", "password"),
                method="pbkdf2"
            ),
            is_admin=True
        )
        db.session.add(admin_user)

        db.session.commit()

        print("Created Database")