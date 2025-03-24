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

    app.register_blueprint(api_main, url_prefix="/api/v1")

    app.register_blueprint(site_auth, url_prefix="/auth")
    app.register_blueprint(site_enrollment, url_prefix="/enrollment")
    app.register_blueprint(site_main, url_prefix="/")

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
        print("Created Database")