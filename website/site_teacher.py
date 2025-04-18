from werkzeug.security import generate_password_hash as gph
from werkzeug.security import check_password_hash as cph
from flask import Blueprint, render_template, request, abort, Response, flash, redirect, url_for
from flask_login import current_user, login_required
from .models import User, Course, Role, roles, Term
from urllib.parse import unquote
from functools import wraps
from sqlalchemy import select
from .helpers import get_courses, is_instructor_for_course
from . import db

site_teacher = Blueprint("site_teacher", __name__)

@site_teacher.route("/Courses")
@login_required
def courses():
    return(render_template("instructor/select_term.html", terms=Term.query.all()))

@site_teacher.route("/Courses/<string:term>")
@login_required
def courses_term(term):
    instructor_role = Role.query.filter_by(name="Instructor").first()
    if not instructor_role:
        flash("Instructor role not found in database.", "error")
        return redirect(url_for('site_main.home'))

    try:
        current_page = max(int(request.args.get("page", 1)), 1)
    except:
        current_page = 1
    try:
        per_page = max(int(request.args.get("per_page", 50)), 1)
    except:
        per_page = 50
    pagination = current_user.get_courses_role(instructor_role, current_page, per_page)
    courses = pagination.items
    total_courses = pagination.total
    total_pages = pagination.pages

    titles = ["ID", "Name", "Department", "Number", "Session", "Units", "Actions"]
    rows = []
    for course in courses:
        if(course.term != term):
            continue
        resign_button = f"""
        <form>
        <input type="hidden" name="from" value="site_instructor.courses">
        <button class="btn btn-danger btn-sm"
                hx-delete="{url_for('api_main.remove_user_role', user_id=current_user.id, course_id=course.id)}"
                hx-target="#courses-content"
                hx-swap="innerHTML"
                hx-headers='{{"Accept": "text/html"}}'
                hx-confirm="Are you sure you want to resign from {course.dept} {course.number}?">
            Resign
        </button>
        </form>
        """
        name = f"""<a href="{url_for("site_teacher.manage_course", course_id=course.id)}">{course.name}</a>"""
        rows.append([
            course.id,
            name,
            course.dept,
            course.number,
            course.session,
            course.units,
            resign_button # Add the button HTML
        ])

    return render_template(
        "instructor/courses.html",
        courses=courses, # Pass the course objects
        rows=rows,
        titles=titles,
        current_page=current_page,
        total_pages=total_pages,
        total_courses=total_courses,
        items_per_page=per_page
    )

@site_teacher.route("/Courses/<int:course_id>/manage")
@login_required
def manage_course(course_id):
    course = Course.query.get_or_404(course_id)

    # --- Authorization Check ---
    if not is_instructor_for_course(current_user, course_id):
        flash("You do not have permission to manage this course.", "error")
        return redirect(url_for('site_teacher.courses')) # Redirect to their course list

    # Fetch paginated students for this course
    page = request.args.get('page', 1, type=int)
    students_pagination = course.get_students_with_grades(page=page, per_page=20) # e.g., 20 students per page

    return render_template(
        "instructor/manage_course.html",
        course=course,
        students_pagination=students_pagination,
        # Pass pagination details needed by the macro
        current_page=students_pagination.page,
        total_pages=students_pagination.pages,
        total_items=students_pagination.total,
        items_per_page=20
    )