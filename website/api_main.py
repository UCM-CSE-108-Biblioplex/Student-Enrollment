from werkzeug.security import check_password_hash as cph
from flask import Blueprint, jsonify, g, request
from flask_login import current_user
from urllib.parse import unquote
from functools import wraps
from .models import User, APIKey

api_main = Blueprint("api_main", __name__)

def requires_authentication(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # requires authentication
        api_key = request.headers.get("X-API-Key", None) or request.args.get("api_key", None)
        if(not api_key and not current_user.is_authenticated):
            return(jsonify({"error": "Authentication required"}), 401)
        
        # api key authentication that will probably never get used lmao
        if(api_key):
            # no user id?
            target_user_id = request.headers.get("X-User-ID", None) or request.args.get("user_id", None)
            if(not target_user_id):
                return(jsonify({"error": "No user specified"}), 400)
            # no user?
            target_user = User.query.get(target_user_id)
            admin_user = User.query.filter_by(is_admin=True).first()
            if(not target_user):
                return(jsonify({"error": "Invalid user"}), 404)
                # is the key valid
            key_checks = [cph(api_key.key) for key in target_user.api_keys + admin_user.api_keys]
            if(not any(key_checks)):
                return(jsonify({"error": "Invalid API Key"}), 403)
            g.user = target_user
            return

        if(current_user.is_authenticated):
            g.user = current_user
            return
        
        return(f(*args, **kwargs))
    return(decorated_function)
        

@api_main.route("/test")
def test():
    return(jsonify({"test": "test"}))

@api_main.route("/username")
def username():
    username = request.args.get("username", "")
    username = unquote(username)
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