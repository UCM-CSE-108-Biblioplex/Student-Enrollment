from flask import Blueprint, jsonify, g, request, abort, Response, render_template, url_for
from werkzeug.security import generate_password_hash as gph
from werkzeug.security import check_password_hash as cph
from flask_login import current_user
from urllib.parse import unquote
from functools import wraps
from .models import User, APIKey, CourseCorequisite, Course, Term, Department
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

@api_main.route("/users", methods=["GET", "PUT", "POST", "DELETE"])
@requires_authentication
def users():
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
        
        users_ = pagination.items
        total_pages = pagination.pages
        total_users = pagination.total
        
        return users_, page, total_pages, total_users, per_page

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
        if (is_admin is not None and is_admin.lower() in ["true", "on", "yes", "1"]):
            target_user.is_admin = is_admin.lower() in ["true", "on", "yes", "1"]
        if(not is_admin):
            target_user.is_admin = False
        
        password = data.get("password", None)
        if(password):
            target_user.password = gph(password)
        
        return(target_user)

    def delete_user(request):
        content_type = request.headers.get("Content-Type")
        if(content_type == "application/x-www-form-urlencoded"):
            data = request.form
        else:
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
    
    def render_users(users_, current_page, total_pages, total_users, per_page):
        def parse_name(user):
            name = user.first_name + " "
            if(user.middle_name):
                name += user.middle_name
                name += " "
            name += user.last_name
            return(name)

        rows = []
        for user in users_:
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
            "macros/users_content.html", 
            users=users_,
            rows=rows,
            titles=titles,
            current_page=current_page,
            total_pages=total_pages,
            total_users=total_users,
            items_per_page=per_page
        )

    if(request.method == "GET"):
        # if you're not admin, you can only GET yourself
        if(not g.user.is_admin):
            return(jsonify(g.user.to_dict()))

        users_, page, total_pages, total_users, per_page = get_users(request)
        
        # Check if the client wants HTML or JSON
        accept_header = request.headers.get('Accept', '')
        if 'text/html' in accept_header:
            # Return HTML for HTMX requests
            return(render_users(users_, page, total_pages, total_users, per_page))
        else:
            # Return JSON for API requests
            response = {
                "users": [user.to_dict() for user in users_],
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
            current_page = new_user.id // 50 + 1
            pagination = User.query.paginate(page=current_page, per_page=50)
            users_ = pagination.items
            total_pages = pagination.pages
            total_users = pagination.total
            return(render_users(users_, current_page, total_pages, total_users, 50))
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
            users_ = pagination.items
            total_pages = pagination.pages
            total_users = pagination.total
            return(render_users(users_, current_page, total_pages, total_users, 50))
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
        except Exception as e:
            db.session.rollback()
            abort(Response(f"A database error occurred: {str(e)}", 500))
        
        accept_header = request.headers.get("Accept", "")
        if("text/html" in accept_header):
            # Return HTML for HTMX requests
            current_page = target_user.id // 50 + 1
            pagination = User.query.paginate(page=current_page, per_page=50)
            users_ = pagination.items
            total_pages = pagination.pages
            total_users = pagination.total
            return(render_users(users_, current_page, total_pages, total_users, 50))
        else:
            return(jsonify(target_user.to_dict()))

@api_main.route("/courses", methods=["GET", "PUT", "POST", "DELETE"])
@requires_authentication
def courses():
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
        
        courses_ = Course.query
        if(term):
            courses_ = courses_.filter_by(term=term)

        # fuzzy search by name
        if(query == "name"):
            course_name = request.args.get("name", "")
            if(course_name):
                courses_ = courses_.filter(Course.name.like(f"%{course_name}%"))
        # search by ID
        elif(query == "id"):
            course_id = request.args.get("id", None)
            try:
                course_id = int(course_id)
            except:
                abort(Response("Invalid course number.", 400))
            if(not course_id):
                abort(Response("ID is required.", 400))
            courses_ = courses_.filter_by(id=course_id)
        # search by course department and number
        else:
            course_dept = request.args.get("dept", None)
            course_num = request.args.get("num", None)
            min_number = request.args.get("min", None)
            max_number = request.args.get("max", None)
            if(course_dept):
                courses_ = courses_.filter_by(course_dept=course_dept)
            if(course_num is not None):
                courses_ = courses_.filter_by(number=course_num)
            if(min_number):
                courses_ = courses_.filter(Course.number >= min_number)
            if(max_number):
                courses_ = courses_.filter(Course.number <= max_number)
            
        # paginate
        pagination = courses_.paginate(page=page, per_page=per_page)
        courses_ = pagination.items
        total_pages = pagination.pages
        total_courses = pagination.total

        # return
        return(courses_, page, total_pages, total_courses, per_page)

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
        
        return(target_course)
        
    def delete_course(request):
        content_type = request.headers.get("Content-Type")
        if("application/x-www-form-urlencoded" in content_type):
            data = request.form
        else:
            data = request.get_json()
        if(data is None):
            abort(Response("No request JSON.", 400))
        
        course_id = data.get("course_id", None)
        if(not course_id):
            abort(Response("Course ID is required.", 400))

        target_course = Course.query.get(course_id)
        if(not target_course):
            abort(Response("User not found", 404))
        
        return(target_course)
    
    def render_courses(courses_, current_page, total_pages, total_courses, per_page):
        titles = ["ID", "Term", "Name", "Department", "Number", "Session", "Units", "Actions"]
        rows = []

        for course in courses_:
            actions = render_template(
                "macros/actions.html",
                model=course,
                endpoint=url_for("api_main.terms"),
                model_type="term"
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
        return(render_template(
            "macros/courses_content.html",
            courses=courses_,
            rows=rows,
            titles=titles,
            current_page=current_page,
            total_pages=total_pages,
            total_courses=total_courses,
            items_per_page=50,
            depts=["CSE", "MATH", "WRI", "PHYS", "CHEM", "ENG", "ENGR", "EE", "EECS", "GASP", "ANTH", "BIOE", "BIO", "CHE", "BCME", "CCST", "CHN", "JPN", "CEE", "COGS", "COMM", "CRS", "CRES", "DSC", "ECON", "EDU", "EH", "ES", "ESS", "FRE", "GEO", "GSTU", "HIS", "HS", "IH", "MGMT", "MBSE", "MSE", "ME", "MIST", "NSE", "PHIL", "POLI", "PSY", "PH", "QSB", "SPRK", "SPAN", "SOC"],
            terms=["F09", "S10", "Su10", "F10", "S11", "Su11", "F11", "S12", "Su12", "F12", "S13", "Su13", "F13", "S14", "Su14", "F14", "S15", "Su15", "F15", "S16", "Su16", "F16", "S17", "Su17", "F17", "S18", "Su18", "F18", "S19", "Su19", "F19", "S20", "Su20", "F20", "S21", "Su21", "F21", "S22", "Su22", "F22", "S23", "Su23", "F23", "S24", "Su24", "F24", "S25", "Su25", "F25"]
        ))

    if(request.method == "GET"):
        courses_, page, total_pages, total_users, per_page = get_courses(request)

        accept_header = request.headers.get("Accept", "")
        if("text/html" in accept_header):
            return(render_courses(courses_, page, total_pages, total_users, per_page))
        else:
            response = {
                "courses": [course.to_dict() for course in courses_],
                "total_pages": total_pages,
                "total_courses": total_courses,
            }
            return(jsonify(response))
    
    if(request.method == "POST"):
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
            current_page = new_course.id // 50 + 1
            pagination = Course.query.paginate(page=current_page, per_page=50)
            courses_= pagination.items
            total_pages = pagination.pages
            total_courses = pagination.total
            return(render_courses(courses_, current_page, total_pages, total_courses, 50))
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
            current_page = target_course.id // 50 + 1
            pagination = Course.query.paginate(page=current_page, per_page=50)
            courses_= pagination.items
            total_pages = pagination.pages
            total_courses = pagination.total
            return(render_courses(courses_, current_page, total_pages, total_courses, 50))
        else:
            return(jsonify(new_course.to_dict()))
    
    if(request.method == "DELETE"):
        if(not g.user.is_admin):
            abort(Response("Insufficient permissions.", 403))

        target_course = delete_course(request)

        try:
            db.session.delete(target_course)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            abort(Response(f"A database error occurred: {str(e)}", 500))
        
        accept_header = request.headers.get("Accept", "")
        if("text/html" in accept_header):
            current_page = target_course.id // 50 + 1
            pagination = Course.query.paginate(page=current_page, per_page=50)
            courses_= pagination.items
            total_pages = pagination.pages
            total_courses = pagination.total
            return(render_courses(courses_, current_page, total_pages, total_courses, 50))
        else:
            return(jsonify(target_course.to_dict()))

@api_main.route("/terms", methods=["POST", "GET", "PUT", "DELETE"])
@requires_authentication
def terms():
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

        # what kind of search are we doing?
        query = request.args.get("query", "name")
        if(query not in ["name", "id"]):
            query = "name"
        
        terms_ = Term.query

        # fuzzy search by name
        if(query == "name"):
            term_name = request.args.get("name", "")
            if(term_name):
                terms_ = terms_.filter(Term.name.like(f"%{term_name}%"))
        # search by ID
        elif(query == "id"):
            term_id = request.args.get("id", None)
            try:
                term_id = int(term_id)
            except:
                abort(Response("Invalid term ID.", 400))
            if(not term_id):
                abort(Response("ID is required.", 400))
            terms_ = terms_.filter_by(id=term_id)
            
        # paginate
        pagination = terms_.paginate(page=page, per_page=per_page)
        terms_ = pagination.items
        total_pages = pagination.pages
        total_terms = pagination.total

        # return
        return(terms_, page, total_pages, total_terms, per_page)

    def create_term(request):
        content_type = request.headers.get("Content-Type")
        if(content_type == "application/x-www-form-urlencoded"):
            data = request.form
        else:
            data = request.get_json()
        if(data is None):
            abort(Response("No request body.", 400))

        term_name = data.get("name", "")
        if(not term_name):
            abort(Response("Term name is required.", 400))
        term_abbreviation = data.get("abbreviation", "")
        if(not term_abbreviation):
            abort(Response("Term abbreviation is required"))
        try:
            term_index = int(data.get("term_index", ""))
        except Exception as e:
            term_index = None
        session = data.get("session", "")
        
        new_term = Term(
            name=term_name,
            abbreviation=term_abbreviation,
            index=term_index
        )
        return(new_term)

    def edit_term(request):
        content_type = request.headers.get("Content-Type")
        if(content_type == "application/x-www-form-urlencoded"):
            data = request.form
        else:
            data = request.get_json()
        
        if(not data):
            abort(Response("No request body.", 400))

        term_id = data.get("term_id", "")
        if(not term_id):
            abort(Response("Term ID is required.", 400))
        try:
            term_id = int(term_id)
        except:
            abort(Response("Invalid term ID.", 400))
        target_term = Term.query.get(term_id)
        if(not target_term):
            abort(Response("Term not found.", 404))

        term_name = data.get("name", "")
        if(term_name):
            target_term.name = term_name
        term_abbreviation = data.get("abbreviation", "")
        if(term_abbreviation):
            target_term.abbreviation = term_abbreviation
        try:
            term_index = int(data.get("term_index", ""))
        except:
            term_index = None
        if(term_index):
            try:
                target_term.index = int(term_index)
            except:
                abort(Response("Invalid term index.", 400))
        

        return(target_term)
        
    def delete_term(request):
        content_type = request.headers.get("Content-Type")
        if(content_type == "application/x-www-form-urlencoded"):
            data = request.form
        else:
            data = request.get_json()
        if(data is None):
            abort(Response("No request JSON.", 400))
        
        term_id = data.get("term_id", None)
        if(not term_id):
            abort(Response("Term ID is required.", 400))
        try:
            term_id = int(term_id)
        except:
            abort(Response("Invalid Term ID", 404))

        target_term = Term.query.get(term_id)
        if(not target_term):
            abort(Response("Term not found", 404))
        
        return(target_term)
    
    def render_terms(terms_, current_page, total_pages, total_terms, per_page):
        titles = ["Index", "ID", "Name", "Abbreviation", "Actions"]
        rows = []

        for term in terms_:
            actions = render_template(
                "macros/actions.html",
                model=term,
                model_type="term",
                endpoint=url_for("api_main.terms"),
                field_name="term_id"
            )
            rows.append([
                term.index,
                term.id,
                term.name,
                term.abbreviation,
                actions
            ])
        return(render_template(
            "macros/terms_content.html",
            terms=terms_,
            rows=rows,
            titles=titles,
            current_page=current_page,
            total_pages=total_pages,
            total_terms=total_terms,
            items_per_page=50
        ))
    if(request.method == "GET"):
        terms_, page, total_pages, total_users, per_page = get_users(request)

        accept_header = request.headers.get("Accept", "")
        if("text/html" in accept_header):
            return(render_terms(terms_, page, total_pages, total_users, per_page))
        else:
            response = {
                "terms": [term.to_dict() for term in terms_],
                "total_pages": total_pages,
                "total_terms": total_term,
            }
            return(jsonify(response))
    
    if(request.method == "POST"):
        if(not g.user.is_admin):
            abort(Response("Insufficient permissions.", 403))
        new_term = create_term(request)
        try:
            db.session.add(new_term)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            abort(Response(f"A database error occured: {str(e)}", 500))
        
        accept_header = request.headers.get("Accept", "")
        if("text/html" in accept_header):
            current_page = new_term.id // 50 + 1
            pagination = Term.query.paginate(page=current_page, per_page=50)
            terms_ = pagination.items
            total_pages = pagination.pages
            total_terms = pagination.total
            return(render_terms(terms_, current_page, total_pages, total_terms, 50))
        else:
            return(jsonify(new_term.to_dict()))
    
    if(request.method == "PUT"):
        if(not g.user.is_admin):
            abort(Response("Insufficient permissions.", 403))
        
        target_term = edit_term(request)
        try:
            db.session.add(target_term)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            abort(Response(f"A database error occured: {str(e)}", 500))
        
        accept_header = request.headers.get("Accept", "")
        if("text/html" in accept_header):
            current_page = target_term.id // 50 + 1
            pagination = Term.query.paginate(page=current_page, per_page=50)
            terms_ = pagination.items
            total_pages = pagination.pages
            total_terms = pagination.total
            return(render_terms(terms_, current_page, total_pages, total_terms, 50))
        else:
            return(jsonify(new_term.to_dict()))
    
    if(request.method == "DELETE"):
        if(not g.user.is_admin):
            abort(Response("Insufficient permissions.", 403))

        target_term = delete_term(request)

        try:
            db.session.delete(target_term)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            abort(Respone("A database error occurred.", 500))

        accept_header = request.headers.get("Accept", "")
        if("text/html" in accept_header):
            current_page = target_term.id // 50 + 1
            pagination = Term.query.paginate(page=current_page, per_page=50)
            titles = ["ID", "Term", "Name", "Department", "Number", "Session", "Units", "Actions"]
            terms_ = pagination.items
            total_pages = pagination.pages
            total_terms = pagination.total
            return(render_terms(terms_, current_page, total_pages, total_terms, 50))
        else:
            return(jsonify(new_term.to_dict()))
    

@api_main.route("/departments", methods=["GET", "PUT", "POST", "DELETE"])
@requires_authentication
def departments():
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

    def create_department(request):
        content_type = request.headers.get("Content-Type")
        if("application/x-www-form-urlencoded" in content_type):
            data = request.form
        else:
            data = request.get_json()
        if(data is None):
            abort(Response("No request body.", 400))
        
        name = data.get("name", "").strip()
        if(not name):
            abort(Response("Department name is required.", 400))
        abbreviation = data.get("abbreviation", "").strip().upper()
        if(not abbreviation):
            abort(Response("Department abbreviation is required.", 400))
        if(len(abbreviation) > 7):
             abort(Response("Abbreviation cannot be longer than 7 characters.", 400))

        # Check if abbreviation already exists
        existing_dept = Department.query.filter_by(abbreviation=abbreviation).first()
        if(existing_dept):
            abort(Response(f"Abbreviation '{abbreviation}' is already in use.", 409)) # 409 Conflict

        new_dept = Department(
            name=name, 
            abbreviation=abbreviation
        )
        return(new_dept)

    def edit_department(request):
        content_type = request.headers.get("Content-Type")
        if("application/x-www-form-urlencoded" in content_type):
            data = request.form
        else:
            data = request.get_json()
        if(not data):
            abort(Response("No request body.", 400))
        
        department_id = data.get("department_id")
        if(not department_id):
            abort(Response("Department ID is required.", 400))
        try:
            department_id = int(department_id)
        except ValueError:
             abort(Response("Invalid Department ID.", 400))

        target_dept = Department.query.get(department_id)
        if(not target_dept):
            abort(Response("Department not found.", 404))
        
        name = data.get("name", "").strip()
        if(name):
            target_dept.name = name
        else:
             abort(Response("Department name cannot be empty.", 400)) # Or skip update if desired

        abbreviation = data.get("abbreviation", "").strip().upper()
        if(abbreviation):
            if len(abbreviation) > 7:
                abort(Response("Abbreviation cannot be longer than 7 characters.", 400))
            # Check if new abbreviation conflicts with another department
            existing_dept = Department.query.filter(
                Department.abbreviation == abbreviation,
                Department.id != department_id # Exclude self
            ).first()
            if(existing_dept):
                 abort(Response(f"Abbreviation '{abbreviation}' is already in use by another department.", 409))
            target_dept.abbreviation = abbreviation
        else:
             abort(Response("Department abbreviation cannot be empty.", 400)) # Or skip update

        return target_dept

    def delete_department(request):
        content_type = request.headers.get("Content-Type")
        # Handle potential differences in content type for DELETE form submission
        if("application/x-www-form-urlencoded" in content_type):
             data = request.form
        else:
            data = request.get_json(silent=True)

        if(data is None):
            abort(Response("No request body.", 400))
        
        department_id = data.get("department_id")

        if(not department_id):
            abort(Response("Department ID is required.", 400))
        try:
            department_id = int(department_id)
        except ValueError:
             abort(Response("Invalid Department ID.", 400))

        target_dept = Department.query.get(department_id)
        if not target_dept:
            abort(Response("Department not found.", 404))
            
        return target_dept
    
    def render_departments(departments_, current_page, total_pages, total_departments, per_page):
        rows = []
        for department in departments_:
            # **Corrected actions macro call**
            actions = render_template(
                "macros/actions.html",
                model=department,
                model_type="department", # Use 'department' as the type
                endpoint=url_for("api_main.departments") 
            )
            rows.append([
                department.id,
                department.name,
                department.abbreviation,
                actions  # Add the generated actions HTML
            ])

        titles = ["ID", "Name", "Abbreviation", "Actions"]
        return(render_template(
            "macros/departments_content.html", 
            departments=departments_,
            rows=rows,
            titles=titles,
            current_page=current_page,
            total_pages=total_pages,
            total_departments=total_departments,
            items_per_page=per_page
        ))

    # --- Route Logic ---
    accept_header = request.headers.get('Accept', '')
    is_htmx_request = 'text/html' in accept_header

    # GET Request
    if(request.method == "GET"):
        # No admin check needed for GET usually, maybe restrict fields later if needed
        departments_, page, total_pages, total_departments, per_page = get_departments(request)
        
        if(is_htmx_request):
            return render_departments(departments_, page, total_pages, total_departments, per_page)
        else:
            response = {
                "departments": [d.to_dict() for d in departments_],
                "current_page": page,
                "total_pages": total_pages,
                "total_departments": total_departments,
                "per_page": per_page
            }
            return(jsonify(response))
    
    # Admin check for modification methods
    if(not current_user.is_admin):
         abort(Response("Insufficient permissions.", 403))

    # POST Request (Create)
    if(request.method == "POST"):
        new_dept = create_department(request)
        try:
            db.session.add(new_dept)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            # Consider logging the error e
            abort(Response(f"A database error occurred: {str(e)}", 500)) 
        
        if(is_htmx_request):
            current_page = new_dept.id // 50 + 1
            pagination = Department.query.paginate(page=current_page, per_page=50)
            departments_ = pagination.items
            total_pages = pagination.pages
            total_departments = pagination.total
            return(render_departments(departments_, current_page, total_pages, total_departments, 50))
        else:
            return(jsonify(new_dept.to_dict()), 201)

    # PUT Request (Edit)
    if(request.method == "PUT"):
        target_dept = edit_department(request)
        try:
            db.session.add(target_dept) # Add works for updates too if obj is tracked
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            abort(Response(f"A database error occurred: {str(e)}", 500))
        
        if(is_htmx_request):
            current_page = target_dept.id // 50 + 1
            pagination = Department.query.paginate(page=current_page, per_page=50)
            departments_ = pagination.items
            total_pages = pagination.pages
            total_departments = pagination.total
            return(render_departments(departments_, current_page, total_pages, total_departments, 50))
        else:
             return jsonify(target_dept.to_dict())

    # DELETE Request
    if(request.method == "DELETE"):
        target_dept = delete_department(request)
        response = target_dept.to_dict()
        try:
            db.session.delete(target_dept)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            abort(Response(f"A database error occurred: {str(e)}", 500))
        
        if(is_htmx_request):
            current_page = target_dept.id // 50 + 1
            pagination = Department.query.paginate(page=current_page, per_page=50)
            departments_ = pagination.items
            total_pages = pagination.pages
            total_departments = pagination.total
            return(render_departments(departments_, current_page, total_pages, total_departments, 50))
        else:
            return(jsonify(response))