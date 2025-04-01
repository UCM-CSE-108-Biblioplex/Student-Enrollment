from flask import Blueprint, render_template
from flask_login import current_user
from functools import wraps

site_admin = Blueprint("site_admin", __name__)

def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if(not current_user.is_authenticated):
            flash("Not Authorized", "error")
            return(redirect(url_for("site_main.home")))
        if(not current_user.is_admin):
            flash("Not Authorized", "error")
            return(redirect(url_for("site_main.home")))
        return(f(*args, **kwargs))
    return(decorated_function)

@site_admin.route("/")
@admin_only
def admin_panel():
    return(render_template("admin_panel.html"))