from flask import Blueprint, jsonify, g, request, abort, Response, render_template
from werkzeug.security import generate_password_hash as gph
from werkzeug.security import check_password_hash as cph
from flask_login import current_user
from urllib.parse import unquote
from functools import wraps
from .models import User, APIKey, CourseCorequisite, Course
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
    content_type = request.headers.get("Content-Type")
    if(content_type == "application/x-www-form-urlencoded"):
        data = request.form
    else:
        data = request.get_json()
    if(data is None):
        abort(Response("No request JSON", 400))
    
    is_admin = data.get("is_admin", False)
    if(is_admin and is_admin is not None):
        is_admin = is_admin.lower() in ["true", "on", "yes", "1"]

    first_name = data.get("first_name", None)
    print(data)
    if(not first_name):
        abort(Response("First name is required.", 400))
    middle_name = data.get("middle_name", "")
    last_name = data.get("last_name", None)
    if(not last_name):
        abort(Response("Last name is required.", 400))
    
    username = data.get("username", None)
    existing_user = User.query.filter_by(username=username).first()
    if(existing_user):
        abort(Response("Username is taken.", 400))
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
    if(not data):
        abort(Response("No request body.", 400))
    
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
        target_user.is_admin = is_admin.lower() in ["true", "on", "yes", "1"]
    
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

def create_course(request):
    content_type = request.headers.get("Content-Type")
    if(content_type == "application/x-www-form-urlencoded"):
        data = request.form
    else:
        data = request.get_json()
    if(data is None):
        abort(Response("No request body.", 400))

    course_term = data.get("term", "")
    if(not course_term):
        abort(Response("Course term is required.", 400))
    course_name = data.get("name", "")
    if(not course_name):
        abort(Response("Course name is required.", 400))
    course_dept = data.get("dept", "")
    if(not course_dept):
        abort(Response("Course department is required.", 400))
    number = data.get("number", "")
    if(not number):
        abort(Response("Course number is required.", 400))
    session = data.get("session", "")
    if(not session):
        abort(Response("Course session is required.", 400))
    units = data.get("units", 0)
    try:
        units = int(units)
    except:
        abort(Response("Invalid course units.", 400))
    
    new_course = Course(
        term=course_term,
        name=course_name,
        dept=course_dept,
        number=number,
        session=session,
        units=units
    )
    return(new_course)

def edit_course(request):
    content_type = request.headers.get("Content-Type")
    if(content_type == "application/x-www-form-urlencoded"):
        data = request.form
    else:
        data = request.get_json()
    
    if(not data):
        abort(Response("No request body.", 400))
    
    course_id = data.get("course_id", None)
    if(not course_id):
        abort(Response("Course ID is required.", 400))
    target_course = Course.query.get(course_id)
    if(not target_course):
        abort(Response("Course not found.", 404))
    
    term = data.get("term", None)
    if(term):
        target_course.term = term[:7]
    name = data.get("name", None)
    if(name):
        target_course.name = name[:255]
    dept = data.get("dept", None)
    if(dept):
        target_course.dept = dept[:7]
    number = data.get("number", None)
    if(number):
        target_course.number = number[:7]
    session = data.get("session", None)
    if(session):
        target_course.session = session[:7]
    units = data.get("units", None)
    if(units):
        try:
            target_course.units = int(units)
        except:
            abort(Response("Invalid course units.", 400))
    
    user_ids = data.get("user_ids", [])
    if(type(user_ids) != list and user_ids is not None):
        abort(Response("Invalid course user_ids", 400))
    if(user_ids):
        for user in target_course.users:
            if(user.id not in user_ids):
                target_course.users.remove(user)
        users = [User.query.get(user_id) for user_id in user_ids]
        for user in users:
            if(user not in target_course.users and user is not None):
                target_course.users.append(user)
    
    # string of form 'DEPT-NUM'
    corequisites = data.get("corequisites", [])
    if(type(corequisites) != list and corequisites is not None):
        abort(Response("Invalid course corequisites", 400))
    if(corequisites):
        try:
            # Luke try not to write utterly unreadable list comprehensions challenge (impossible):
            corequisites = [{"dept": split[0], "number": split[1]} for split in [coreq.split("-") for coreq in corequisites]]
        except:
            abort(Response())
        course_corequisites = [coreq.to_dict() for coreq in target_course.corequisites]
        for corequisite in corequisites:
            if(type(corequisite) != dict):
                abort(Response("Invalid course corequisites", 400))
            if(corequesitie in course_corequisites):
                continue
            new_corequisite = CourseCorequisite(
                course=target_course,
                dept=corequisite["dept"],
                number=corequisite["number"]
            )
            db.session.add(new_corequisite)
        for corequisite in target_course.corequisites:
            if(corequisite.to_dict() not in corequisites):
                target_course.corequisites.remove(corequisite)

    prerequisites = data.get("prerequisites", [])
    if(type(prerequisites) != list and prerequisites is not None):
        abort(Response("Invalid course prerequisites", 400))
    if(prerequisites):
        try:
            # Luke try not to write utterly unreadable list comprehensions challenge (impossible):
            prerequisites = [{"dept": split[0], "number": spit[1]} for split in [prereq.split("-") for prereq in prerequisites]]
        except:
            abort(Response())
        course_prerequisites = [prereq.to_dict() for prereq in target_course.prerequisites]
        for prerequisite in prerequisites:
            if(type(prerequisite) != dict):
                abort(Response("Invalid course prerequisites", 400))
            if(prerequesitie in course_prerequisites):
                continue
            new_prerequisite = CoursePrerequisite(
                course=target_course,
                dept=prerequisite["dept"],
                number=prerequisite["number"]
            )
            db.session.add(new_prerequisite)
        for prerequisite in target_course.prerequisites:
            if(prerequisite.to_dict() not in prerequisites):
                target_course.prerequisites.remove(prerequisite)
    
    # I'll do schedules later

@api_main.route("/users", methods=["GET", "PUT", "POST", "DELETE"])
@requires_authentication
def users():
    if(request.method == "GET"):
        # if you're not admin, you can only GET yourself
        if(not g.user.is_admin):
            return(jsonify(g.user.to_dict()))

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
            response = {
                "users": [user.to_dict() for user in users],
                "total_pages": total_pages,
                "total_users": total_users
            }
            return jsonify(response)
    
    # create new user
    if(request.method == "POST"):
        # only admins can create users via api
        # anyone can sign up, though
        if(not g.user.is_admin):
            abort(Response("Insufficient permissions.", 403))

        new_user = create_user(request)
        try:
            db.session.add(new_user)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            abort(Response(f"A database error occurred: {str(e)}", 500))
        
        accept_header = request.headers.get("Accept", "")
        if("text/html" in accept_header):
            # Return HTML for HTMX requests
            current_page = new_user.id // 50 + 1
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
            return(jsonify(new_user.to_dict()))
    
    # edit user
    if(request.method == "PUT"):
        target_user = edit_user(request)

        # you can't edit someone else unless you're admin
        if(not g.user.is_admin and g.user.id != target_user.id):
            db.session.rollback()
            abort(Response("Insufficient permissions.", 403))
        
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

        # only admins can delete users via api
        if(not g.user.is_admin):
            abort(Response("Insufficient permissions.", 403))

        try:
            db.session.delete(target_user)
            db.session.commit()
            return jsonify({"success": "User deleted."})
        except Exception as e:
            db.session.rollback()
            abort(Response(f"A database error occurred: {str(e)}", 500))

@api_main.route("/courses", methods=["GET", "PUT", "POST", "DELETE"])
@requires_authentication
def courses():
    if(request.method == "GET"):
        courses, current_page, total_pages, total_courses, per_page = get_courses(request)

        accept_header = request.headers.get("Accept", "")
        if("text/html" in accept_header):
            return("uuuh")
        
        else:
            response = {
                "courses": [course.to_dict() for course in courses],
                "total_pages": total_pages,
                "total_courses": total_courses,
            }
            return(jsonify(response))
    
    if(request.method == "POST"):
        print("post")
        if(not g.user.is_admin):
            abort(Response("Insufficient permissions.", 403))
        new_course = create_course(request)
        try:
            db.session.add(new_course)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            abort(Response(f"A database error occured: {str(e)}", 500))
        
        accept_header = request.headers.get("Accept", "")
        if("text/html" in accept_header):
            current_page = new_course.id // 5 + 1
            pagination = Course.query.paginate(page=current_page, per_page=50)
            courses= pagination.items
            titles = ["ID", "Term", "Name", "Department", "Number", "Session", "Units", "Actions"]
            total_pages = pagination.pages
            total_courses = pagination.total
            rows = []

            for course in courses:
                action_button = f"""<button class="btn btn-primary" onclick="document.querySelector('#course-{course.id}-modal').click()">Edit</button>"""
                rows.append([
                    course.id,
                    course.term,
                    course.name,
                    course.dept,
                    course.number,
                    course.session,
                    course.units,
                    action_button
                ])
            return(render_template(
                "macros/courses_content.html",
                courses=courses,
                rows=rows,
                titles=titles,
                current_page=current_page,
                total_pages=total_pages,
                total_courses=total_courses,
                items_per_page=50,
                depts=["CSE", "MATH", "WRI", "PHYS", "CHEM", "ENG", "ENGR", "EE", "EECS", "GASP", "ANTH", "BIOE", "BIO", "CHE", "BCME", "CCST", "CHN", "JPN", "CEE", "COGS", "COMM", "CRS", "CRES", "DSC", "ECON", "EDU", "EH", "ES", "ESS", "FRE", "GEO", "GSTU", "HIS", "HS", "IH", "MGMT", "MBSE", "MSE", "ME", "MIST", "NSE", "PHIL", "POLI", "PSY", "PH", "QSB", "SPRK", "SPAN", "SOC"],
                terms=["F09", "S10", "Su10", "F10", "S11", "Su11", "F11", "S12", "Su12", "F12", "S13", "Su13", "F13", "S14", "Su14", "F14", "S15", "Su15", "F15", "S16", "Su16", "F16", "S17", "Su17", "F17", "S18", "Su18", "F18", "S19", "Su19", "F19", "S20", "Su20", "F20", "S21", "Su21", "F21", "S22", "Su22", "F22", "S23", "Su23", "F23", "S24", "Su24", "F24", "S25", "Su25", "F25"]
            ))
        else:
            return(jsonify(new_course.to_dict()))
    
    if(request.method == "PUT"):
        if(not g.user.is_admin):
            abort(Response("Insufficient permissions.", 403))
        
        target_course = edit_course(request)
        try:
            db.session.add(new_course)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            abort(Response(f"A database error occured: {str(e)}", 500))
        
        accept_header = request.headers.get("Accept", "")
        if("text/html" in accept_header):
            current_page = target_course.id // 5 + 1
            pagination = Course.query.paginate(page=current_page, per_page=50)
            courses= pagination.items
            titles = ["ID", "Term", "Name", "Department", "Number", "Session", "Units", "Actions"]
            total_pages = pagination.pages
            total_courses = pagination.total
            rows = []

            for course in courses:
                action_button = f"""<button class="btn btn-primary" onclick="document.querySelector('#course-{course.id}-modal').click()">Edit</button>"""
                rows.append([
                    course.id,
                    course.term,
                    course.name,
                    course.dept,
                    course.number,
                    course.session,
                    course.units,
                    action_button
                ])
            return(render_template(
                "macros/.html",
                courses=courses,
                rows=rows,
                titles=titles,
                current_page=current_page,
                total_pages=total_pages,
                total_courses=total_courses,
                items_per_page=50,
                depts=["CSE", "MATH", "WRI", "PHYS", "CHEM", "ENG", "ENGR", "EE", "EECS", "GASP", "ANTH", "BIOE", "BIO", "CHE", "BCME", "CCST", "CHN", "JPN", "CEE", "COGS", "COMM", "CRS", "CRES", "DSC", "ECON", "EDU", "EH", "ES", "ESS", "FRE", "GEO", "GSTU", "HIS", "HS", "IH", "MGMT", "MBSE", "MSE", "ME", "MIST", "NSE", "PHIL", "POLI", "PSY", "PH", "QSB", "SPRK", "SPAN", "SOC"],
                terms=["F09", "S10", "Su10", "F10", "S11", "Su11", "F11", "S12", "Su12", "F12", "S13", "Su13", "F13", "S14", "Su14", "F14", "S15", "Su15", "F15", "S16", "Su16", "F16", "S17", "Su17", "F17", "S18", "Su18", "F18", "S19", "Su19", "F19", "S20", "Su20", "F20", "S21", "Su21", "F21", "S22", "Su22", "F22", "S23", "Su23", "F23", "S24", "Su24", "F24", "S25", "Su25", "F25"]
            ))
        else:
            return(jsonify(new_course.to_dict()))

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
