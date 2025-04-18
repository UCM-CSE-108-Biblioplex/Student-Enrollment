from flask_login import current_user
from flask import Blueprint, render_template

site_main = Blueprint("site_main", __name__)

@site_main.route("/")
def home():
    return(render_template("index.html"))