from werkzeug.security import generate_password_hash as gph
from werkzeug.security import check_password_hash as cph
from flask import Blueprint, render_template, request, abort, Response, flash, redirect, url_for
from flask_login import current_user
from urllib.parse import unquote
from functools import wraps
from .models import User, Course, Term, Department
from . import db

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

def get_terms(request):
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
    name = request.args.get("name", None)
    
    if(name):
        name = unquote(name)
        pagination = User.query.filter(
            Term.name.like(f"%{name}%")
        ).paginate(
            page=page,
            per_page=per_page
        )
    else:
        pagination = Term.query.paginate(page=page, per_page=per_page)
    
    terms = pagination.items
    total_pages = pagination.pages
    total_terms = pagination.total
    
    return terms, page, total_pages, total_terms, per_page
def get_departments(request):
    try:
        page = request.values.get("page", 1, type=int)
    except ValueError:
        page = 1
    try:
        per_page = request.values.get("per_page", 50, type=int)
    except ValueError:
        per_page = 50
    
    search_term = request.values.get("search", None)
    
    query = Department.query

    if(search_term):
        search_term_like = f"%{search_term}%"
        query = query.filter(
            db.or_(
                Department.name.like(search_term_like),
                Department.abbreviation.like(search_term_like)
            )
        ).order_by(Department.name)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    departments_ = pagination.items
    total_pages = pagination.pages
    total_departments = pagination.total
    
    # Return the correct page number requested, handles potential out-of-bounds from error_out=False
    current_page = page if page <= total_pages else total_pages 
    if(current_page < 1): current_page = 1 # Ensure page is at least 1

    return(departments_, current_page, total_pages, total_departments, per_page)

@site_admin.route("/")
def admin_panel():
    return(render_template("admin_panel.html"))

@site_admin.route("/Users")
def users():
    if(not current_user.is_authenticated or not current_user.is_admin):
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
        actions = render_template(
            "macros/actions.html",
            model=user,
            endpoint=url_for("api_main.users"),
            model_type="user"
        )
        rows.append([
            user.id,
            user.username,
            parse_name(user),
            user.email,
            "Yes" if user.is_admin else "No",
            actions
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
    if(not current_user.is_authenticated or not current_user.is_admin):
        flash("You don't have permission to access this page.", "error")
        return(redirect(url_for("site_main.home")))
    
    courses, page, total_pages, total_courses, per_page = get_courses(request)
    rows = []
    for course in courses:
        actions = render_template(
            "macros/actions.html",
            model=course,
            endpoint=url_for("api_main.courses"),
            model_type="course"
        )
        rows.append([
            course.id,
            course.term,
            course.name,
            course.dept,
            course.number,
            course.session,
            course.units,
            actions
        ])
    titles = ["ID", "Term", "Name", "Department", "Number", "Session", "Units", "Actions"]

    depts = [d for d in Department.query.order_by(Department.abbreviation).all()]
    terms = [t for t in Term.query.order_by(Term.index).all()]

    return(render_template(
        "admin_courses.html",
        courses=courses,
        rows=rows,
        titles=titles,
        current_page=page,
        total_pages=total_pages,
        total_courses=total_courses,
        items_per_page=per_page,
        depts=depts,
        terms=terms
    ))

@site_admin.route("/Terms")
def terms():
    if(not current_user.is_authenticated or not current_user.is_admin):
        flash("You don't have permission to access this page.", "error")
        return(redirect(url_for("site_main.home")))
    
    terms_, page, total_pages, total_terms, per_page = get_terms(request)
    rows = []

    for term in terms_:
        actions = render_template(
            "macros/actions.html",
            model=term,
            endpoint=url_for("api_main.terms"),
            model_type="term"
        )
        rows.append([
            term.index,
            term.id,
            term.name,
            term.abbreviation,
            actions
        ])
    
    titles = ["Index", "ID", "Name", "Abbreviation", "Actions"]

    return(render_template(
        "admin_terms.html",
        terms=terms_,
        rows=rows,
        titles=titles,
        current_page=page,
        total_pages=total_pages,
        total_terms=total_terms,
        items_per_page=per_page,
    ))

@site_admin.route("/Departments")
def departments():
    if(not current_user.is_admin):
        flash("You don't have permission to access this page.", "error")
        return(redirect(url_for("site_main.home")))
    
    departments_, page, total_pages, total_departments, per_page = get_departments(request)
    rows = []

    for department in departments_:
        actions = render_template(
            "macros/actions.html",
            model=department,
            endpoint=url_for("api_main.departments"),
            model_type="department"
        )
        rows.append([
            department.id,
            department.name,
            department.abbreviation,
            actions
        ])
    
    titles = ["ID", "Name", "Abbreviation", "Actions"]

    return(render_template(
        "admin_departments.html",
        departments=departments_,
        rows=rows,
        titles=titles,
        current_page=page,
        total_pages=total_pages,
        total_departments=total_departments,
        items_per_page=per_page
    ))