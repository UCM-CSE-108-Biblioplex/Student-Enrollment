from werkzeug.security import generate_password_hash as gph
from werkzeug.security import check_password_hash as cph
from flask import Blueprint, render_template, request, jsonify, abort, Response
from flask_login import current_user
from urllib.parse import unquote
from functools import wraps
from .models import User

site_admin = Blueprint("site_admin", __name__)

def get_users(request):
    try:
        page = request.args.get("page", 1)
        page = int(page)
    except:
        page = 1
    try:
        per_page = request.args.get("per_page", 50)
        per_page = int(per_page)
    except:
        per_page = 50
    
    # get matching students
    username = request.args.get("username", None)
    
    if(username):
        username = unquote(username)
        pagination = User.query.filter(
            User.username.like(f"%{username}%")
        ).paginate(
            page=page,
            per_page=per_page
        )
    else:
        pagination = User.query.paginate(page=page, per_page=per_page)
    
    users = pagination.items
    total_pages = pagination.pages
    total_users = pagination.total
    
    return users, page, total_pages, total_users

@site_admin.route("/")
def admin_panel():
    return(render_template("admin_panel.html"))

@site_admin.route("/Users")
def users():
    if not current_user.is_admin:
        flash("You don't have permission to access this page.", "error")
        return redirect(url_for('site_main.home'))
    
    # Initial load of users
    users, current_page, total_pages, total_users = get_users(request)

    def parse_name(user):
        name = user.first_name + " "
        if(user.middle_name):
            name += user.middle_name
            name += " "
        name += user.last_name
        return(name)

    rows = []
    for user in users:
        action_button = f"""<button class="btn btn-primary btn-sm" onclick="document.getElementById('user-{user.id}-modal').click()">Edit</button>"""
        rows.append([
            user.id,
            user.username,
            parse_name(user),
            user.email,
            "Yes" if user.is_admin else "No",
            action_button
        ])

    titles = ["ID", "Username", "Name", "Email", "Admin", "Actions"]
    
    return render_template(
        "admin_users.html", 
        users=users,
        rows=rows,
        titles=titles,
        current_page=current_page,
        total_pages=total_pages,
        total_users=total_users,
        items_per_page=50
    )
