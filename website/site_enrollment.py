from flask import Blueprint, render_template

site_enrollment = Blueprint("site_enrollment", __name__)

@site_enrollment.route("/Test")
def test():
    return("Test")