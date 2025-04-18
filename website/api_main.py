from flask import Blueprint, jsonify, g, request, abort, Response, render_template, url_for
from werkzeug.security import check_password_hash as cph
from sqlalchemy import select, delete, insert, update
from datetime import datetime, timedelta
from functools import wraps

from .models import User, APIKey, CourseCorequisite, Course, Term, Department, CoursePrerequisite, Role, roles
from .helpers import *
from . import db

import secrets

api_main = Blueprint("api_main", __name__)

def requires_authentication(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if(current_user.is_authenticated):
            g.user = current_user
            return(f(*args, **kwargs))

        # requires authentication
        api_key = request.headers.get("X-API-Key", None)
        if(not api_key):
            abort(Response("Authentication required.", 401))
        
        # api key authentication that will probably never get used lmao
        # no user id?
        target_user_id = request.headers.get("X-User-ID", None)
        if(not target_user_id):
            abort(Response("User ID is required.", 400))
        # no user?
        target_user = User.query.get(target_user_id)
        if(not target_user):
            abort(Response("User not found", 404))
        # is the key valid
        key_checks = [cph(api_key, key.key) for key in target_user.api_keys]
        if(not any(key_checks)):
            abort(Response("Invalid API Key", 403))
        g.user = target_user
        return(f(*args, **kwargs))
    return(decorated_function)

@api_main.route("/api-key", methods=["GET"])
@requires_authentication
def api_keys():
    api_key = secrets.token_urlsafe(32)
    expiry = datetime.utcnow() + timedelta(days=60)
    new_key = APIKey(
        user=g.user,
        is_admin=g.user.is_admin,
        key=api_key,
        expiry=expiry
    )
    return(render_template(
        "keys_content.html",
        text_to_copy = api_key
    ))

@api_main.route("/users", methods=["GET", "PUT", "POST", "DELETE"])
@requires_authentication
def users():
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

@api_main.route("/users/<int:user_id>/roles", methods=["POST"])
@requires_authentication
def add_user_role(user_id):
    # ... (permission checks, data validation, database logic - unchanged) ...
    if not g.user.is_admin and not g.user.id == user_id: 
        abort(Response("Insufficient permissions.", 403))
    target_user = User.query.get_or_404(user_id)
    course_id = request.form.get("course_id")
    role_id = request.form.get("role_id")
        
    if not course_id or not role_id:
        abort(Response("Course ID and Role ID are required.", 400))
    try:
        course_id = int(course_id)
        role_id = int(role_id)
    except ValueError:
        abort(Response("Invalid Course ID or Role ID.", 400))

    course = Course.query.get(course_id)
    role = Role.query.get(role_id)
    if not course or not role:
        abort(Response("Course or Role not found.", 404))

    # only admins can assign non-student roles
    if(role.name != "Student" and not g.user.is_admin):
        abort(Response("Insufficient permissions.", 403))
    if(role.name == "Student" and course.get_students_with_grades().total >= course.maximum):
        abort(Response("Course full.", 403))
    
    existing_assignment = db.session.execute(select(roles).where(roles.c.user_id == user_id, roles.c.course_id == course_id)).first()
    try:
        if existing_assignment:
            if existing_assignment.role_id != role_id:
                 stmt = roles.update().where(roles.c.user_id == user_id, roles.c.course_id == course_id).values(role_id=role_id)
                 db.session.execute(stmt)
                 operation_type = "updated"
            else: operation_type = "unchanged"
        else:
            stmt = roles.insert().values(user_id=user_id, course_id=course_id, role_id=role_id)
            db.session.execute(stmt)
            operation_type = "added"
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        abort(Response(f"Database error: {str(e)}", 500))

    # --- Response Handling ---
    accept_header = request.headers.get('Accept', '')
    is_htmx_request = 'text/html' in accept_header

    db.session.refresh(target_user)
    current_assignments = target_user.get_role_assignments()

    if is_htmx_request:
        db.session.refresh(target_user)
        request_from = request.form.get("from", None)
        term = Term.query.filter_by(abbreviation=course.term).first()
        try:
            current_page = max(int(request.args.get("page", 1)), 1)
        except:
            current_page = 1
        try:
            per_page = max(int(request.args.get("per_page", 50)), 1)
        except:
            per_page = 50
        if(request_from == "site_instructor.courses"):
            return(render_instructor_courses(
                current_user,
                term,
                current_page,
                per_page
            ))
        if(request_from == "site_enrollment.enroll_term"):
            return(render_student_courses(
                current_user,
                term,
                current_page,
                per_page
            ))
        if(request_from == "site_admin.user_roles"):
            current_assignments = target_user.get_role_assignments()
            all_courses = Course.query.order_by(Course.term, Course.dept, Course.number).all()
            assignable_roles = Role.query.filter(Role.name.in_(['Student', 'Instructor', 'TA'])).all()
            modal_content_id = f'user-roles-modal-content-{user_id}'
            # *** RENDER THE SPECIFIC TEMPLATE ***
            return render_template(
                "render_user_roles_content.html",
                user=target_user,
                current_assignments=current_assignments,
                all_courses=all_courses,
                assignable_roles=assignable_roles,
                modal_content_id=modal_content_id
            )
        return("Unknown request origin.")
    else:
        formatted_assignments = [{"course": c.to_dict(), "role": r.to_dict()} for c, r in current_assignments]
        return jsonify({"message": f"Role assignment {operation_type}.", "user_id": user_id, "assignments": formatted_assignments}), 200

@api_main.route("/users/<int:user_id>/roles/<int:course_id>", methods=["DELETE"])
@requires_authentication
def remove_user_role(user_id, course_id):
    if not g.user.is_admin and g.user.id != user_id:
        abort(Response("Insufficient permissions.", 403))
    target_user = User.query.get_or_404(user_id)

    assignment_to_delete = db.session.query(roles).filter(
        roles.c.user_id == user_id,
        roles.c.course_id == course_id
    ).first()

    if not assignment_to_delete:
        abort(Response("No such assignment.", 404))

    deleted_course = Course.query.get(assignment_to_delete.course_id)
    deleted_role = Role.query.get(assignment_to_delete.role_id)
    try:
        stmt = delete(roles).where(roles.c.user_id == user_id, roles.c.course_id == course_id)
        result = db.session.execute(stmt)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        abort(Response(f"Database error: {str(e)}", 500))

    # --- Response Handling ---
    accept_header = request.headers.get('Accept', '')
    is_htmx_request = 'text/html' in accept_header

    if is_htmx_request:
        db.session.refresh(target_user)
        request_from = request.form.get("from", None)
        term = Term.query.filter_by(abbreviation=deleted_course.term).first()
        try:
            current_page = max(int(request.args.get("page", 1)), 1)
        except:
            current_page = 1
        try:
            per_page = max(int(request.args.get("per_page", 50)), 1)
        except:
            per_page = 50
        if(request_from == "site_instructor.courses"):
            return(render_instructor_courses(
                current_user,
                term,
                current_page,
                per_page
            ))
        if(request_from == "site_enrollment.enroll_term"):
            return(render_student_courses(
                current_user,
                term,
                current_page,
                per_page
            ))
        if(request_from == "site_admin.user_roles"):
            current_assignments = target_user.get_role_assignments()
            all_courses = Course.query.order_by(Course.term, Course.dept, Course.number).all()
            assignable_roles = Role.query.filter(Role.name.in_(['Student', 'Instructor', 'TA'])).all()
            modal_content_id = f'user-roles-modal-content-{user_id}'
            # *** RENDER THE SPECIFIC TEMPLATE ***
            return render_template(
                "render_user_roles_content.html",
                user=target_user,
                current_assignments=current_assignments,
                all_courses=all_courses,
                assignable_roles=assignable_roles,
                modal_content_id=modal_content_id
            )
        return("Unknown request origin")
    else:
        # Return JSON (unchanged)
        if not hasattr(Role, 'to_dict'):
             def role_to_dict(self): return {'id': self.id, 'name': self.name}
             Role.to_dict = role_to_dict
        formatted_deleted = {"course": deleted_course.to_dict(), "role": deleted_role.to_dict()}
        return jsonify({"message": "Role assignment removed.", "user_id": user_id, "deleted_assignment": formatted_deleted}), 200

@api_main.route("/courses", methods=["GET", "PUT", "POST", "DELETE"])
@requires_authentication
def courses():
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
            db.session.add(target_course)
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
            return(jsonify(target_course.to_dict()))
    
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

# not quite DRY but I don't get paid enough for that
# wait, I don't get paid at all...
@api_main.route("/catalog")
def catalog():
    print(request.args)
    print(request.form)

    courses = Course.query
    term = request.args.get("term", None) or request.form.get("term", None)
    if(term):
        courses = courses.filter_by(term=term)
    department = request.form.get("subject", None) or request.args.get("subject", None)
    if(department):
        courses = courses.filter_by(dept=department)
    course_number = request.form.get("number", None) or request.args.get("number", None)
    if(course_number):
        courses = courses.filter_by(number=course_number)
    page = request.args.get("page", 1) or request.form.get("page", 1)
    try:
        page = int(page)
    except:
        page = 1
    per_page = request.args.get("per_page", 50) or request.form.get("per_page", 50)
    try:
        per_page = int(per_page)
    except:
        per_page = 1
    
    pagination = courses.paginate(page=page, per_page=per_page)
    total_courses = pagination.total
    total_pages = pagination.pages
    courses = pagination.items
    print(courses)

    accept_header = request.headers.get("Accept", "")
    if("text/html" in accept_header):
        titles = ["ID", "Term", "Name", "Department", "Number", "Session", "Units"]
        rows = []

        for course in courses:
            rows.append([
                course.id,
                course.term,
                course.name,
                course.dept,
                course.number,
                course.session,
                course.units,
            ])
        depts = [d for d in Department.query.all()]
        terms = [t for t in Term.query.all()]
        return(render_template(
            "macros/enrollment/catalog_content.html",
            courses=courses,
            rows=rows,
            titles=titles,
            current_page=page,
            total_pages=total_pages,
            total_courses=total_courses,
            items_per_page=per_page,
        ))
    else:
        response = {
            "courses": [course.to_dict() for course in courses],
            "total_pages": total_pages,
            "total_courses": total_courses,
        }
        return(jsonify(response))

@api_main.route("/courses/<int:course_id>/students/<int:student_id>/grade", methods=["PUT"])
@requires_authentication
def update_student_grade(course_id, student_id):
    # ... (authentication, validation, database logic - unchanged) ...
    if not is_instructor_for_course(g.user, course_id) and not g.user.is_admin:
        abort(Response("Insufficient permissions. Must be instructor for this course.", 403))
    new_grade = request.form.get("grade")
    if new_grade is None:
        abort(Response("Grade value is required.", 400))

    student_role = Role.query.filter_by(name="Student").first()
    if not student_role:
        abort(Response("Student role definition not found.", 500))

    assignment = db.session.execute(select(roles).where(roles.c.user_id == student_id, roles.c.course_id == course_id, roles.c.role_id == student_role.id)).first()
    if not assignment:
        abort(Response("Student enrollment record not found for this course.", 404))
    try:
        stmt = update(roles).where(roles.c.user_id == student_id, roles.c.course_id == course_id).values(grade=new_grade if new_grade != "" else None)
        db.session.execute(stmt)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        abort(Response(f"Database error updating grade: {str(e)}", 500))

    # --- Response Handling ---
    accept_header = request.headers.get('Accept', '')
    is_htmx_request = 'text/html' in accept_header

    if is_htmx_request:
        course = Course.query.get_or_404(course_id)
        try: page = int(request.form.get("current_page", 1))
        except ValueError: page = 1
        students_pagination = course.get_students_with_grades(page=page, per_page=20)
        # *** RENDER THE SPECIFIC TEMPLATE ***
        return render_template(
            "render_student_list_content.html", # Use the specific template
            course=course,
            students_pagination=students_pagination
        )
    else:
        # Return JSON (unchanged)
        student = User.query.get(student_id)
        return jsonify({"message": "Grade updated successfully.", "course_id": course_id, "student_id": student_id, "student_username": student.username if student else "N/A", "new_grade": new_grade if new_grade != "" else None}), 200
    
@api_main.route("/courses/<int:course_id>/students/<int:student_id>", methods=["DELETE"])
@requires_authentication
def remove_student_from_course(course_id, student_id):
    # ... (authentication, validation, database logic - unchanged) ...
    if not is_instructor_for_course(g.user, course_id): abort(Response("Insufficient permissions. Must be instructor for this course.", 403))
    target_user = User.query.get_or_404(student_id)
    assignment_to_delete = db.session.query(Course, Role).join(roles, Course.id == roles.c.course_id).join(Role, Role.id == roles.c.role_id).filter(roles.c.user_id == student_id, roles.c.course_id == course_id).first()

    if not assignment_to_delete:
         accept_header = request.headers.get('Accept', '')
         is_htmx_request = 'text/html' in accept_header
         if is_htmx_request:
             course = Course.query.get_or_404(course_id)
             page = 1
             students_pagination = course.get_students_with_grades(page=page, per_page=20)
             # *** RENDER THE SPECIFIC TEMPLATE ***
             return render_template("render_student_list_content.html", course=course, students_pagination=students_pagination)
         else:
             return jsonify({"message": "Student enrollment not found or already removed."}), 200

    deleted_course, deleted_role = assignment_to_delete
    if deleted_role.name != "Student": abort(Response("This action can only remove students.", 403))
    try:
        stmt = delete(roles).where(roles.c.user_id == student_id, roles.c.course_id == course_id)
        result = db.session.execute(stmt)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        abort(Response(f"Database error removing student: {str(e)}", 500))

    # --- Response Handling ---
    accept_header = request.headers.get('Accept', '')
    is_htmx_request = 'text/html' in accept_header

    if is_htmx_request:
        course = Course.query.get_or_404(course_id)
        page = 1
        students_pagination = course.get_students_with_grades(page=page, per_page=20)
        # *** RENDER THE SPECIFIC TEMPLATE ***
        return render_template(
            "render_student_list_content.html",
            course=course,
            students_pagination=students_pagination,
        )
    else:
        # Return JSON (unchanged)
        if not hasattr(Role, 'to_dict'):
             def role_to_dict(self): return {'id': self.id, 'name': self.name}
             Role.to_dict = role_to_dict
        formatted_deleted = {"course": deleted_course.to_dict(), "role": deleted_role.to_dict()}
        return jsonify({"message": "Student removed from course.", "course_id": course_id, "removed_student_id": student_id, "removed_student_username": target_user.username, "removed_assignment": formatted_deleted}), 200

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
                "macros/admin/actions.html",
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
            "macros/admin/terms_content.html",
            terms=terms_,
            rows=rows,
            titles=titles,
            current_page=current_page,
            total_pages=total_pages,
            total_terms=total_terms,
            items_per_page=50
        ))
    if(request.method == "GET"):
        terms_, page, total_pages, total_terms, per_page = get_terms(request)

        accept_header = request.headers.get("Accept", "")
        if("text/html" in accept_header):
            return(render_terms(terms_, page, total_pages, total_terms, per_page))
        else:
            response = {
                "terms": [term.to_dict() for term in terms_],
                "total_pages": total_pages,
                "total_terms": total_terms,
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
            abort(Response("A database error occurred.", 500))

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