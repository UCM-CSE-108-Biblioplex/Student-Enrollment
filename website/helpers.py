from werkzeug.security import generate_password_hash as gph
from flask import abort, Response, render_template
from urllib.parse import unquote

from .models import *
import re

# username generation
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

# user utils
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
        # this password cannot collide with hashed passwords thanks to salts
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

# course utils
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
    maximum = data.get("max", None)
    if(not maximum):
        abort(Response("Maximum students is required.", 400))
    try:
        maximum = int(maximum)
    except:
        abort(Response("Invalid course maximum.", 400))
    
    new_course = Course(
        term=course_term,
        name=course_name,
        dept=course_dept,
        number=number,
        session=session,
        units=units,
        maximum=maximum
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
            if(corequisite in course_corequisites):
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
            prerequisites = [{"dept": split[0], "number": split[1]} for split in [prereq.split("-") for prereq in prerequisites]]
        except:
            abort(Response())
        course_prerequisites = [prereq.to_dict() for prereq in target_course.prerequisites]
        for prerequisite in prerequisites:
            if(type(prerequisite) != dict):
                abort(Response("Invalid course prerequisites", 400))
            if(prerequisite in course_prerequisites):
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

def render_courses(courses, current_page, total_pages, total_courses, per_page):
    titles = ["ID", "Term", "Name", "Department", "Number", "Session", "Units", "Actions"]
    rows = []

    for course in courses:
        actions = render_template(
            "macros/admin/actions.html",
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
    depts = [d for d in Department.query.all()]
    terms = [t for t in Term.query.all()]
    return(render_template(
        "macros/admin/courses_content.html",
        courses=courses,
        rows=rows,
        titles=titles,
        current_page=current_page,
        total_pages=total_pages,
        total_courses=total_courses,
        items_per_page=per_page,
        depts=depts,
        terms=terms
    ))

# render helpers
def render_admin_users(users, current_page, total_pages, total_users, per_page):
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
            "macros/admin/actions.html",
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
        "macros/admin/users_content.html", 
        users=users,
        rows=rows,
        titles=titles,
        current_page=current_page,
        total_pages=total_pages,
        total_users=total_users,
        items_per_page=per_page
    )

def render_instructor_courses(instructor, current_page, per_page):
    titles = ["ID", "Name", "Department", "Number", "Session", "Units", "Actions"]
    rows = []

    pagination = instructor.get_courses_role(current_page, per_page)
    total_pages = pagination.pages
    total_courses = pagination.total
    courses = pagination.items

    for course in courses:
        resign_button = f"""
        <button class="btn btn-danger btn-sm"
            hx-delete="{url_for('api_main.remove_user_role', user_id=instructor.id, course_id=course.id)}"
            hx-target="#courses-content"
            hx-swap="innerHTML"
            hx-headers='{{"Accept": "text/html"}}'
            hx-confirm="Are you sure you want to resign from {course.dept} {course.number}?">
            Resign
        </button>
        """
        rows.append([
            course.id,
            course.name,
            course.dept,
            course.number,
            course.session,
            course.units,
            resign_button # Add the button HTML
        ])
    
    return(render_template(
        "macros/instructor/courses_content.html",
        rows=rows,
        titles=titles,
        courses=courses,
        current_page=current_page,
        total_pages=total_pages,
        total_courses=total_courses,
        items_per_page=per_page
    ))

def is_instructor_for_course(user, course_id):
    instructor_role = Role.query.filter_by(name="Instructor").first()
    if not instructor_role: return False # Should not happen

    assignment = db.session.execute(
        select(roles).where(
            roles.c.user_id == user.id,
            roles.c.course_id == course_id,
            roles.c.role_id == instructor_role.id
        )
    ).first()
    return assignment is not None