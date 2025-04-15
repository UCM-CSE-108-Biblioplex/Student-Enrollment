from werkzeug.security import generate_password_hash as gph
from werkzeug.security import check_password_hash as cph
from flask import Blueprint, render_template, request, abort, Response, flash, redirect, url_for
from flask_login import current_user, login_required
from urllib.parse import unquote
from functools import wraps
from .models import User, Course, Role

site_teacher = Blueprint("site_teacher", __name__)

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

@site_teacher.route("/Courses")
@login_required # Ensure only logged-in users can access
def courses():
    instructor_role = Role.query.filter_by(name="Instructor").first()
    if not instructor_role:
        flash("Instructor role not found in database.", "error")
        return redirect(url_for('site_main.home'))
    
    def generate_instructor_rows(instructor_user, courses):
        rows = []
        for course in courses:
            resign_button = f"""
            <button class="btn btn-danger btn-sm"
                    hx-delete="{url_for('api_main.remove_user_role', user_id=instructor_user.id, course_id=course.id)}"
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
        return rows


    instructor_courses = current_user.get_courses_role(instructor_role)

    # Use the helper function to generate rows with the resign button
    rows = generate_instructor_rows(current_user, instructor_courses)

    titles = ["ID", "Name", "Department", "Number", "Session", "Units", "Actions"]

    # Simplified pagination data since we're showing all courses for the instructor
    current_page = 1
    total_courses = len(instructor_courses)
    items_per_page = total_courses if total_courses > 0 else 1 # Avoid division by zero
    total_pages = 1

    return render_template(
        "instructor/courses.html",
        courses=instructor_courses, # Pass the course objects
        rows=rows,
        titles=titles,
        current_page=current_page,
        total_pages=total_pages,
        total_courses=total_courses,
        items_per_page=items_per_page
    )