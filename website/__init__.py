from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from dotenv import load_dotenv
from flask import Flask
import os

load_dotenv()

db = SQLAlchemy()

FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY")
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

    from .models import User

    login_manager = LoginManager()
    login_manager.login_view = "site_auth.login"
    login_manager.init_app(app)

    create_database(app)

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
        admin_role = Role(name="Admin")
        db.session.add(admin_role)

        # user-defined roles
        # in case of unforeseen use cases (e.g., Learning Assistent, etc.)
        defined_roles = os.getenv("EXTRA_ROLES", None)
        if(defined_roles):
            defined_roles = defined_roles.split(",")
            for role in defined_roles:
                new_role = Role(name=role)
                db.session.add(new_roll)

        admin_iser = User(
            username=os.environ.get("DEFAULT_ADMIN_USERNAME", "admin"),
            password=generate_password_hash(
                os.environ.get("DEFAULT_ADMIN_PASSWORD", "password"),
                method="pbkdf2",
                role=admin_role
            ),

        )

        db.session.commit()

        print("Created Database")