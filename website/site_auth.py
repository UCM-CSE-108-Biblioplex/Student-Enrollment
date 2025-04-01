from werkzeug.security import generate_password_hash as gph
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, login_user
from .models import User, Role
from . import db

site_auth = Blueprint("site_auth", __name__)

@site_auth.route("/Signup", methods=["GET", "POST"])
def signup():
    if(request.method == "POST"):
        first_name = request.form.get("first_name")
        if(not first_name):
            flash("First Name is required.", "warning")
        middle_name = request.form.get("middle_name")
        last_name = request.form.get("last_name")
        if(not last_name):
            flash("Last Name is required.", "warning")
        username = request.form.get("username")
        if(not username):
            flash("Username is required.", "warning")
        email = request.form.get("email")
        if(not email):
            flash("Email is required.", "warning")
        password1 = request.form.get("password1")
        if(not password1):
            flash("Password is required.", "warning")
        password2 = request.form.get("password2")
        if(not password2):
            flash("Password Confirmation is required.", "warning")
        if(password1 != password2):
            flash("Passwords do not match", "warning")
        
        if(not all([first_name, last_name, username, email, password1, password2, password1 == password2])):
            return(redirect(url_for("site_auth.signup")))
        
        existing_user = User.query.filter_by(username=username).first()
        if(existing_user):
            flash("Username is taken.", "warning")
            return(redirect(url_for("site_auth.signup")))

        try:
            new_user = User(
                username=username,
                email=email,
                password=gph(password1, method="pbkdf2")
            )
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            flash(f"Welcome, {first_name}", "success")
            return(redirect(url_for("site_main.home")))
        except Exception as e:
            print(e)
            flash("A database error occurred.", "error")
            return(redirect(url_for("site_auth.signup")))
        
    return(render_template("signup.html"))

@site_auth.route("/Login", methods=["GET", "POST"])
def login():
    # will return an HTML form that allows users
    # to input information to login with

    # submitted form sends a POST request
    # server validates username/email, password
    # maybe 2FA
    return(render_template("login.html"))

@site_auth.route("/My-Account")
@login_required
def myaccount():
    # may not be necessary
    return 404