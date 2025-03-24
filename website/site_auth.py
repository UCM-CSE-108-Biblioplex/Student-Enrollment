from flask import Blueprint, render_template

site_auth = Blueprint("site_auth", __name__)

@site_auth.route("/Signup", methods=["GET", "POST"])
def signup():
    # will return an HTML form that allows users
    # to input information they want to sign up with

    # submitted form sends a POST request
    # server validates username, email are available
    # validates password and creates a new user, assigning an ID
    # redirects user, message flashing to show login success/failure

    # maybe requires email/phone validation, 2FA
    return(render_template("signup.html"))

@site_auth.route("/Login", methods=["GET", "POST"])
def login():
    # will return an HTML form that allows users
    # to input information to login with

    # submitted form sends a POST request
    # server validates username/email, password
    # maybe 2FA
    return(render_template("login.html"))