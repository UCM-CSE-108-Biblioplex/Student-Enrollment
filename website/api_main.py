from flask import Blueprint, jsonify

api_main = Blueprint("api_main", __name__)

@api_main.route("/test")
def test():
    return(jsonify({"test": "test"}))