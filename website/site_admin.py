from werkzeug.security import generate_password_hash as gph
from werkzeug.security import check_password_hash as cph
from flask import Blueprint, render_template, request, abort, Response, flash, redirect, url_for
from flask_login import current_user
from urllib.parse import unquote
from functools import wraps
from .models import User, Course

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
    
    return users, page, total_pages, total_users, per_page

def get_courses(request):
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

    # what kind of search are we doing?
    query = request.args.get("query", "name")
    if(query not in ["name", "id", "dept"]):
        query = "name"
    # specific term?
    term = request.args.get("term", None)
    
    courses = Course.query
    if(term):
        courses = courses.filter_by(term=term)

    # fuzzy search by name
    if(query == "name"):
        course_name = request.args.get("name", "")
        if(course_name):
            courses = courses.filter(Course.name.like(f"%{course_name}%"))
    # search by ID
    elif(query == "id"):
        course_id = request.args.get("id", None)
        try:
            course_id = int(course_id)
        except:
            abort(Response("Invalid course number.", 400))
        if(not course_id):
            abort(Response("ID is required.", 400))
        courses = courses.filter_by(id=course_id)
    # search by course department and number
    else:
        course_dept = request.args.get("dept", None)
        course_num = request.args.get("num", None)
        min_number = request.args.get("min", None)
        max_number = request.args.get("max", None)
        if(course_dept):
            courses = courses.filter_by(course_dept=course_dept)
        if(course_num is not None):
            courses = courses.filter_by(number=course_num)
        if(min_number):
            courses = courses.filter(Course.number >= min_number)
        if(max_number):
            courses = courses.filter(Course.number <= max_number)
        
    # paginate
    pagination = courses.paginate(page=page, per_page=per_page)
    courses = pagination.items
    total_pages = pagination.pages
    total_courses = pagination.total

    # return
    return(courses, page, total_pages, total_courses, per_page)

@site_admin.route("/")
def admin_panel():
    return(render_template("admin_panel.html"))

@site_admin.route("/Users")
def users():
    if not current_user.is_admin:
        flash("You don't have permission to access this page.", "error")
        return redirect(url_for('site_main.home'))
    
    # Initial load of users
    users, current_page, total_pages, total_users, per_page = get_users(request)

    def parse_name(user):
        name = user.first_name + " "
        if(user.middle_name):
            name += user.middle_name
            name += " "
        name += user.last_name
        return(name)

    rows = []
    for user in users:
        action_button = f"""<button class="btn btn-primary" onclick="document.getElementById('user-{user.id}-modal').click()">Edit</button>"""
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
        items_per_page=per_page
    )

@site_admin.route("/Courses")
def courses():
    if(not current_user.is_admin):
        flash("You don't have permission to access this page.", "error")
        return(Redirect(url_for("site_main.home")))
    
    courses, page, total_pages, total_courses, per_page = get_courses(request)
    rows = []
    for course in courses:
        action_button = f"""<button class="btn btn-primary" onclick="document.querySelector('#course-{course.id}-modal').click()">Edit</button>"""
        rows.append([
            course.id,
            course.name,
            course.dept,
            course.number,
            course.session,
            course.units,
            action_button
        ])
    titles = ["ID", "Name", "Department", "Number", "Session", "Units", "Actions"]

    return(render_template(
        "admin_courses.html",
        courses=courses,
        rows=rows,
        titles=titles,
        current_page=page,
        total_pages=total_pages,
        total_courses=total_courses,
        items_per_page=per_page
    ))