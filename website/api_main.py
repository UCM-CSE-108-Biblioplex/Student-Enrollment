from flask import Blueprint, jsonify, g, request, abort, Response, render_template
from werkzeug.security import generate_password_hash as gph
from werkzeug.security import check_password_hash as cph
from flask_login import current_user
from urllib.parse import unquote
from functools import wraps
from .models import User, APIKey
from . import db
import re

api_main = Blueprint("api_main", __name__)

def requires_authentication(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if(current_user.is_authenticated):
            g.user = current_user

        # requires authentication
        api_key = request.headers.get("X-API-Key", None)
        if(not api_key and not current_user.is_authenticated):
            abort(Response("Authentication required.", 401))
        
        # api key authentication that will probably never get used lmao
        if(api_key):
            # no user id?
            target_user_id = request.headers.get("X-User-ID", None)
            if(not target_user_id):
                abort(Response("User ID is required.", 400))
            # no user?
            target_user = User.query.get(target_user_id)
            if(not target_user):
                abort(Response("User not found", 404))
                # is the key valid
            key_checks = [cph(api_key.key, key) for key in target_user.api_keys]
            if(not any(key_checks)):
                abort(Response("Invalid API Key", 403))
            g.user = target_user
        return(f(*args, **kwargs))
    return(decorated_function)

# copy/pasted from site_auth.py; maybe reuse
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
    
    return username

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
    
    return users, page, total_pages, total_users, per_page

def create_user(request):
    data = request.get_json()
    if(data is None):
        abort(Response("No request JSON", 400))
    
    is_admin = data.get("is_admin", False)

    first_name = data.get("first_name", None)
    if(not first_name):
        abort(Response("First name is required.", 400))
    middle_name = data.get("middle_name", "")
    last_name = data.get("last_name", None)
    if(not last_name):
        abort(Response("Last name is required.", 400))
    
    username = data.get("username", None)
    if(not username):
        username = generate_username(first_name, middle_name, last_name)
    email = data.get("email", None)
    if(not email):
        abort(Response("Email is required.", 400))
    password = data.get("password", None)

    new_user = User(
        is_admin=is_admin,
        first_name=first_name,
        middle_name=middle_name,
        last_name=last_name,
        username=username,
        email=email,
        password=gph(password) if password else "needsnewpassword"
        # this password cannot collide with hashed passwords
    )
    return(new_user)

def edit_user(request):
    content_type = request.headers.get("Content-Type")
    if(content_type == "application/x-www-form-urlencoded"):
        data = request.form
    else:
        data = request.get_json()
    if(data is None):
        abort(Response("No request JSON.", 400))
    
    # get user
    user_id = data.get("user_id", None)
    if(not user_id):
        abort(Response("User ID is required.", 400))
    target_user = User.query.get(user_id)
    if(not target_user):
        abort(Response("User not found", 404))
    
    first_name = data.get("first_name", None)
    if(first_name):
        target_user.first_name = first_name
    middle_name = data.get("middle_name", None)
    if(middle_name is not None):  # Allow empty string
        target_user.middle_name = middle_name
    last_name = data.get("last_name", None)
    if(last_name):
        target_user.last_name = last_name
    
    username = data.get("username", None)
    if(username):
        existing_user = User.query.filter_by(username=username).first()
        if(existing_user and existing_user.id != target_user.id):
            abort(Response("Username is already taken", 400))
        target_user.username = username
    generate_new_username = data.get("generate_new_username", False)
    if(generate_new_username):
        first_name = target_user.first_name
        middle_name = target_user.middle_name
        last_name = target_user.last_name
        target_user.username = generate_username(first_name, middle_name, last_name)
    email = data.get("email", None)
    if(email):
        existing_user = User.query.filter_by(email=email).first()
        if(existing_user and existing_user.id != target_user.id):
            abort(Response("Email is in use by another user.", 400))
        target_user.email = email
    
    is_admin = data.get("is_admin")
    if is_admin is not None:
        target_user.is_admin = is_admin
    
    password = data.get("password", None)
    if(password):
        target_user.password = gph(password)
    
    return(target_user)

def delete_user(request):
    data = request.get_json()
    if(data is None):
        abort(Response("No request JSON.", 400))
    
    user_id = data.get("user_id", None)
    if(not user_id):
        abort(Response("User ID is required.", 400))

    target_user = User.query.get(user_id)
    if(not target_user):
        abort(Response("User not found", 404))
    
    return(target_user)    

@api_main.route("/users", methods=["GET", "PUT", "POST", "DELETE"])
# @requires_authentication
def users():
    # if(not g.user.is_admin): # placeholder for now
    #     abort(Response("Insufficient permissions.", 403))
    
    if(request.method == "GET"):
        users, current_page, total_pages, total_users, per_page = get_users(request)
        
        # Check if the client wants HTML or JSON
        accept_header = request.headers.get('Accept', '')
        if 'text/html' in accept_header:
            # Return HTML for HTMX requests
            def parse_name(user):
                name = user.first_name + " "
                if(user.middle_name):
                    name += user.middle_name
                    name += " "
                name += user.last_name
                return(name)

            rows = []
            for user in users:
                # Create a button that will trigger the modal
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
                "macros/users_content.html", 
                users=users,
                rows=rows,
                titles=titles,
                current_page=current_page,
                total_pages=total_pages,
                total_users=total_users,
                items_per_page=per_page
            )
        else:
            # Return JSON for API requests
            return jsonify([user.to_dict() for user in users])
    
    # create new user
    if(request.method == "POST"):
        new_user = create_user(request)
        try:
            db.session.add(new_user)
            db.session.commit()
            return(jsonify(new_user.to_dict()))
        except Exception as e:
            db.session.rollback()
            abort(Response(f"A database error occurred: {str(e)}", 500))
    
    # edit user
    if(request.method == "PUT"):
        target_user = edit_user(request)
        try:
            db.session.add(target_user)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            abort(Response(f"A database error occurred: {str(e)}", 500))
        
        accept_header = request.headers.get("Accept", "")
        if("text/html" in accept_header):
            # Return HTML for HTMX requests
            current_page = target_user.id // 50 + 1
            pagination = User.query.paginate(page=current_page, per_page=50)
            users = pagination.items
            titles = ["ID", "Username", "Name", "Email", "Admin", "Actions"]
            total_pages = pagination.pages
            total_users = pagination.total
            rows = []

            def parse_name(user):
                name = user.first_name + " "
                if(user.middle_name):
                    name += user.middle_name
                    name += " "
                name += user.last_name
                return(name)
                
            for user in users:
                # Create a button that will trigger the modal
                action_button = f"""<button class="btn btn-primary btn-sm" onclick="document.getElementById('user-{user.id}-modal').click()">Edit</button>"""
                rows.append([
                    user.id,
                    user.username,
                    parse_name(user),
                    user.email,
                    "Yes" if user.is_admin else "No",
                    action_button
                ])

            return render_template(
                "macros/users_content.html", 
                users=users,
                rows=rows,
                titles=titles,
                current_page=current_page,
                total_pages=total_pages,
                total_users=total_users,
                items_per_page=50
            )
        else:
            return(jsonify(target_user.to_dict()))
    
    # delete user
    if(request.method == "DELETE"):
        target_user = delete_user(request)
        try:
            db.session.delete(target_user)
            db.session.commit()
            return jsonify({"success": "User deleted."})
        except Exception as e:
            db.session.rollback()
            abort(Response(f"A database error occurred: {str(e)}", 500))

@api_main.route("/username")
def username():
    username = unquote(request.args.get("username", ""))
    matching_users = User.query.filter_by(username=username).first()
    if(matching_users):
        return(jsonify({"valid": False}))
    else:
        return(jsonify({"valid": True}))

@api_main.route("/classes/", methods=["GET", "PUT", "POST", "DELETE"])
@requires_authentication
def classes():
    # GET: returns a user's enrollment in a given term
    # PUT: update enrollment status (e.g., P/NP -> Letter Grade)
    # POST: enroll in a class
    # DELETE: Drop/Withdraw from class
    return 404

@api_main.route("/catalog", methods=["GET"])
def catalog():
    # GET: returns available classes for a given term
    # maybe we can add creation/deletion of classes to the tool
    return 404