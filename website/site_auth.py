from flask import Blueprint, render_template

site_auth = Blueprint("site_auth", __name__)

@site_auth.route("/Signup", methods=["GET", "POST"])
def signup():
    return(render_template("signup.html"))

@site_auth.route("/Login", methods=["GET", "POST"])
def login():
    return(render_template("login.html"))