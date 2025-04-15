from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from werkzeug.security import generate_password_hash as gph
from werkzeug.security import check_password_hash as cph
from flask_login import login_required, login_user, current_user, logout_user
from .models import User, Role
from . import db
import re

site_auth = Blueprint("site_auth", __name__)

def validate_signup(request):
    errors = []

    first_name = request.form.get("first_name")
    if(not first_name):
        errors.append("First Name is required.")
    if(len(first_name) > 255):
        errors.append("First name must be fewer than 256 characters.")

    middle_name = request.form.get("middle_name", "")
    if(len(middle_name) > 255):
        errors.append("Middle name must be fewer than 256 characters.")

    last_name = request.form.get("last_name")
    if(not last_name):
        errors.append("Last Name is required.")
    if(len(last_name) > 255):
        errors.append("Last name must be fewer than 256 characters.")

    username = request.form.get("username", "")
    if(username and len(username) > 255):
        errors.append("Username must be fewer than 256 characters.")

    email = request.form.get("email")
    if(not email):
        errors.append("Email is required.")
    if(len(email) > 255):
        errors.append("Email must be fewer than 256 characters.")

    password1 = request.form.get("password1")
    if(not password1):
        errors.append("Password is required.")
    if(len(password1) < 6 or len(password1) > 255):
        errors.append("Password must be at lest 6 characters and fewer than 256 characters long.")

    password2 = request.form.get("password2")
    if(not password2):
        errors.append("Password Confirmation is required.")
    if(password1 != password2):
        errors.append("Passwords do not match")
    
    return(errors)

def generate_username(first_name, middle_name, last_name):
    # generate username
    # Just the user's last name, alphanumeric
    
    processed_last_name = username = re.sub(r"r[^a-zA-Z0-9]", "", last_name.casefold().capitalize())

    # if that's taken, add middle initial (if provided) and last initial
    results = User.query.filter_by(username=username)
    if(len(results.all()) > 0):
        last_initial = re.sub(r"r[^a-zA-Z0-9]", "", last_name.casefold().capitalize())[:1]
        if(middle_name): # if middle name is provided
            middle_initial = re.sub(r"r[^a-zA-Z0-9]", "", middle_name.casefold().capitalize())[:1]
            processed_last_name = processed_last_name[:-2]
        else: # otherwise just last initial
            middle_initial = ""
            processed_last_name = processed_last_name[:-1]
        username = processed_last_name + middle_initial + last_initial
    
    # if that's taken, add a number
    results = User.query.filter_by(username=username)
    if(len(results.all()) > 0):
        number = str(len(results.all()))
        slice_index = -1 * len(number)
        processed_last_name = processed_last_name[:slice_index]
        username = processed_last_name + middle_initial + last_initial + number
    
    return(username)

@site_auth.route("/Signup", methods=["GET", "POST"])
def signup():
    if(request.method == "POST"):
        # validate form data
        errors = validate_signup(request)

        first_name = request.form.get("first_name")
        middle_name = request.form.get("middle_name", "")
        last_name = request.form.get("last_name")
        username = request.form.get("first_name", "")
        email = request.form.get("email")
        password = request.form.get("password1")

        # is it all there?
        if(errors):
            for error in errors:
                flash(error, "warning")
            return(redirect(url_for("site_auth.signup")))
        
        # make sure username is unique; generate username if none is provided
        if(username and len(username) > 4):
            existing_user = User.query.filter_by(username=username).first()
            if(existing_user):
                flash("Username is taken.", "warning")
                return(redirect(url_for("site_auth.signup")))
        else:
            if(username and len(username) < 4):
                flash("Username must be at least 4 characters; generating valid username.", "warning")
            username = generate_username(first_name, middle_name, last_name)
            flash(f"Your username is {username}. Save it for later.", "success")

        # create new user
        try:
            new_user = User(
                first_name=first_name,
                middle_name=middle_name if middle_name else None,
                last_name=last_name,
                username=username,
                email=email,
                password=gph(password, method="pbkdf2")
            )
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)
            flash(f"Welcome, {first_name}", "success")
            return(redirect(url_for("site_main.home")))
        except Exception as e:
            print(e)
            db.session.rollback()
            flash(f"A database error occurred. ({e})", "error")
            return(redirect(url_for("site_auth.signup")))
        
    return(render_template("signup.html"))

@site_auth.route("/Login", methods=["GET", "POST"])
def login():
    if(request.method == "POST"):
        # get form data
        username = request.form.get("username")
        if(not username):
            flash("Username/Email is required.", "warning")
        password = request.form.get("password")
        if(not password):
            flash("Password is required.", "warning")
        if(not all([username, password])):
            return(redirect(url_for("site_auth.login")))
        
        # find user
        user = User.query.filter_by(username=username).first()
        if(not user):
            user = User.query.filter_by(email=username).first()
        if(not user):
            flash("Username/Email not associated with an account. Sign Up!", "warning")
            return(redirect(url_for("site_auth.login")))
        
        # check password
        if(cph(user.password, password)):
            login_user(user, remember=True)
            flash(f"Welcome back, {user.first_name}.", "success")
            return(redirect(url_for("site_main.home")))
        else:
            flash(f"Invalid password.", "warning")
            return(redirect(url_for("site_auth.login")))

    return(render_template("login.html"))

@site_auth.route("/Logout")
@login_required
def logout():
    logout_user()
    flash("Logged out.", "success")
    return(redirect(url_for("site_main.home")))

@site_auth.route("/My-Account")
@login_required
def my_account():
    # may not be necessary
    return 404