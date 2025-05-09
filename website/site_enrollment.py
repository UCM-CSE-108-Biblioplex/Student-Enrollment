from flask import Blueprint, render_template, request, url_for
from flask_login import login_required, current_user, current_user
from .models import Course, Term, Department, Role, Role, roles
from sqlalchemy import select
from . import db

site_enrollment = Blueprint("site_enrollment", __name__, url_prefix="/enrollment")

@site_enrollment.route("/")
def enrollment():
    return("Endpoint Incomplete", 404)

@site_enrollment.route("/Classes")
@login_required
def classes():
    terms = Term.query.all()
    return(render_template("enrollment/schedule_select_term.html", terms=terms))

@site_enrollment.route("/Classes/<string:term>")
@login_required
def classes_term(term):
    student_role = Role.query.filter_by(name="Student").first()

    try:
        current_page = int(request.args.get("current_page", 1))
    except:
        current_page = 1
    try:
        per_page = request.args.get("per_page", 50)
    except:
        per_page = 50
    pagination = current_user.get_courses_role(student_role, current_page, per_page)
    courses = pagination.items
    total_courses = pagination.total
    total_pages = pagination.pages

    titles = ["ID", "Name", "Department", "Number", "Session", "Units", "Students"]
    rows = []
    for course in courses:
        rows.append([
            course.id,
            course.name,
            course.dept,
            course.number,
            course.session,
            course.units,
            f"{course.get_students_with_grades().total}/{course.maximum}",
        ])

    return render_template(
        "enrollment/course_schedule.html",
        courses=courses, # Pass the course objects
        rows=rows,
        titles=titles,
        current_page=current_page,
        total_pages=total_pages,
        total_courses=total_courses,
        items_per_page=per_page
    )

@site_enrollment.route("/Catalog")
def catalog():
    terms = Term.query.all()
    return(render_template("catalog/catalog.html", terms=terms))

@site_enrollment.route("/Catalog/<string:term>", methods = ['POST', 'GET'])
def catalog_term(term):
    term = Term.query.filter_by(abbreviation=term).first_or_404()
    departments = Department.query.order_by(Department.abbreviation).all()

    # form data
    department = request.args.get("subject", None) or request.form.get("subject", None)
    course_number = request.args.get("number", None) or request.form.get("number", None)
    
    try:
        course_number = int(course_number)
    except:
        course_number = None
    course_id = request.args.get("course_id", None) or request.form.get("course_id", None)

    current_page = request.args.get("page", 1) or request.form.get("page", 1)
    try:
        current_page = int(current_page)
    except:
        current_page = 1
    per_page = request.args.get("per_page", 50) or request.form.get("per_page", 50)
    try:
        per_page = int(per_page)
    except:
        per_page = 50

    courses = Course.query

    if course_id:
        courses = [courses.get_or_404(course_id)]
        total_courses = 1
        total_pages = 1
    else:
        courses = courses.filter_by(term=term.abbreviation)

        if department:
            courses = courses.filter_by(dept=department)
        if course_number:
            courses = courses.filter_by(number=str(course_number))

        pagination = courses.paginate(page=current_page, per_page=per_page)
        total_pages = pagination.pages
        courses = pagination.items
        total_courses = pagination.total

    titles = ["ID", "Term", "Name", "Department", "Number", "Session", "Units", "Students"]
    rows = []
    for course in courses:
        modal_html =  f"""<a @click="document.querySelector('#course-{course.id}-modal').click()">{course.name}</a>"""
        rows.append([
            course.id,
            course.term,
            modal_html,
            course.dept,
            course.number,
            course.session,
            course.units,
            f"{course.get_students_with_grades().total}/{course.maximum}",
        ])

    return render_template(
        "catalog/courses.html",
        term=term,
        departments=departments,
        current_page=current_page,
        total_pages=total_pages,
        total_courses=total_courses,
        items_per_page=per_page,
        rows=rows,
        titles=titles,
        courses=courses
    )

@site_enrollment.route("/Enroll")
@login_required
def enroll():
    # just a page with links to different
    # site_enrollment.enroll_term endpoints
    # maybe use a carousel; maybe use a dropdown; idk
    terms = Term.query.all()
    return(render_template("enrollment/enroll.html", terms=terms))
    
@site_enrollment.route("/Enroll/<string:term>", methods = ['POST', 'GET'])
@login_required
def enroll_term(term):
    term = Term.query.filter_by(abbreviation=term).first_or_404()
    departments = Department.query.order_by(Department.abbreviation).all()

    # form data
    department = request.args.get("subject", None) or request.form.get("subject", None)
    course_number = request.args.get("number", None) or request.form.get("number", None)
    
    try:
        course_number = int(course_number)
    except:
        course_number = None
    course_id = request.args.get("course_id", None) or request.form.get("course_id", None)

    current_page = request.args.get("page", 1) or request.form.get("page", 1)
    try:
        current_page = int(current_page)
    except:
        current_page = 1
    per_page = request.args.get("per_page", 50) or request.form.get("per_page", 50)
    try:
        per_page = int(per_page)
    except:
        per_page = 50

    courses = Course.query

    if course_id:
        courses = [courses.get_or_404(course_id)]
        total_courses = 1
        total_pages = 1
    else:
        courses = courses.filter_by(term=term.abbreviation)

        if department:
            courses = courses.filter_by(dept=department)
        if course_number:
            courses = courses.filter_by(number=str(course_number))

        pagination = courses.paginate(page=current_page, per_page=per_page)
        total_pages = pagination.pages
        courses = pagination.items
        total_courses = pagination.total

    titles = ["ID", "Term", "Name", "Department", "Number", "Session", "Units", "Students", "Add"]
    rows = []
    student_role_id = Role.query.filter_by(name="Student").first().id
    for course in courses:
        existing_assignment = db.session.query(roles).filter(roles.c.user_id == current_user.id, roles.c.course_id == course.id).first()
        if(course.get_students_with_grades().total >= course.maximum):
            button = "<span>(Course Full)</span>"
        elif(existing_assignment):
            button = f'''
                <form id="enroll-button">
                <input type="hidden" name="from" value="site_enrollment.enroll_term">
                <button 
                    class="btn btn-danger" 
                    hx-delete="{url_for("api_main.remove_user_role", user_id=current_user.id, course_id=course.id)}"
                    hx-target="#catalog-content"
                    hx-headers='{{"Accept": "text/html"}}'
                    hx-swap="innerHTML">
                    Leave
                </button>
                </form>'''
        else:
            button = f'''
            <form id="enroll-button">
            <input
                type="hidden"
                id="course-{course.id}-id"
                name="course_id"
                value="{course.id}">
            <input
                type="hidden"
                id="course-{course.id}-id"
                name="role_id"
                value="{student_role_id}">
            <input type="hidden" name="from" value="site_enrollment.enroll_term">
            <button 
                class="btn btn-primary" 
                hx-post="{url_for("api_main.add_user_role", user_id=current_user.id)}"
                hx-target="#catalog-content"
                hx-headers='{{"Accept": "text/html"}}'
                hx-swap="innerHTML">
                Enroll
            </button>
            </form>'''
        modal_html =  f"""<a @click="document.querySelector('#course-{course.id}-modal').click()">{course.name}</a>"""
        rows.append([
            course.id,
            course.term,
            modal_html,
            course.dept,
            course.number,
            course.session,
            course.units,
            f"{course.get_students_with_grades().total}/{course.maximum}",
            button
    ])


    return render_template(
        "enrollment/courses.html",
        term=term,
        departments=departments,
        current_page=current_page,
        total_pages=total_pages,
        total_courses=total_courses,
        items_per_page=per_page,
        rows=rows,
        titles=titles,
        courses=courses
    )