from werkzeug.security import generate_password_hash as gph
from werkzeug.security import check_password_hash as cph
from flask import Blueprint, render_template, request, jsonify, abort, Response
from flask_login import current_user
from urllib.parse import unquote
from functools import wraps
from .models import User

site_admin = Blueprint("site_admin", __name__)

@site_admin.route("/")
def admin_panel():
    return(render_template("admin_panel.html"))

@site_admin.route("/Users")
def users():
    return(render_template("admin_users.html"))