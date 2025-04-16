from flask import Blueprint, render_template, request
from flask_login import login_required
from .models import Course, Term, Department

site_enrollment = Blueprint("site_enrollment", __name__, url_prefix="/enrollment")

@site_enrollment.route("/Test")
def test():
    return("Endpoint Incomplete", 404)

@site_enrollment.route("/")
def enrollment():
    # Options are
    #   - see enrolled classes (select term)
    #   - see available classes (select term)
    #       - includes # of enrolled students
    #       - includes available seats, waitlist slots
    #   - go to enrollment tool
    return("Endpoint Incomplete", 404)

@site_enrollment.route("/Classes")
@login_required
def classes():
    # just a page with links to different
    # site_enrollment.classes_term endpoints
    # maybe use a dropdown; maybe use a carousel; idk
     return("Endpoint Incomplete", 404)

@site_enrollment.route("/Classes/<string:term>")
@login_required
def classes_term(term):
    # returns a calendar displaying term schedule
    #   - contains class schedule + lectures
    #   - ability to download for input into Google
    #       Calendare, etc. would be nice
    # also returns a list of enrolled classes
    # has link to enroll in courses for this term
    return("Endpoint Incomplete", 404)

@site_enrollment.route("/catalog")
def catalog():
    terms = Term.query.all()
    return(render_template("enrollment/catalog.html", terms=terms))


# returns a list of courses offered
#   - includes course name, ID, CRN, etc.
#   - includes instructorm TAs
#   - includes Dates/Times of classes, exams
#       - hovercard w/ calendar element would be neat
#   - includes level of enrollment, waitlist availability
@site_enrollment.route("/catalog/<string:term>", methods = ['POST', 'GET'])
def catalog_term(term):
    # stuff
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
    try:
        course_id = course_id
    except:
        course_id = None
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
    if(course_id):
        courses = [courses.get_or_404(course_id)]
    else:
        if(department):
            courses = courses.filter_by(department=department)
        if(course_number):
            courses = courses.filter_by(number=number)
        pagination = courses.paginate(page=current_page, per_page=per_page)
        total_pages = pagination.pages
        courses = pagination.items
        total_courses = pagination.total

    if(not current_page):
        current_page=1
    total_pages

    titles = ["ID", "Term", "Name", "Department", "Number", "Session", "Units"]
    rows = []
    for course in courses:
        rows.append([
            course.id,
            course.term,
            f"""<a @click="document.querySelector('#course-{course.id}-modal').click()">{course.name}</a>""",
            course.dept,
            course.number,
            course.session,
            course.units
        ])

    return render_template(
        "courses.html",
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
    return(render_template("termSelection.html"))


# likely includes reuised components from
# `catalog_term` and `classes_term` pages
# has a course catalog and calendar of selected term
# checks enrollment availability before allowing db changes
# maybe include prerequisites/restrictions
    
@site_enrollment.route("/Enroll/<string:term>", methods = ['POST', 'GET'])
@login_required
def enroll_term(term):
    subjectData = (request.form.get("subject") or request.args.get("subject") or "").strip()
    courseID = (request.form.get("course") or request.args.get("course") or "").strip()

    query = Course.query.filter_by(term=term)
    

    if subjectData and not courseID:
        query = query.filter(Course.dept.ilike(f"%{subjectData}%"))
    elif courseID and not subjectData:
        query = query.filter(Course.number == courseID)
    elif subjectData and courseID:
        query = query.filter(Course.dept.ilike(f"%{subjectData}%"), Course.number == courseID)

    courses_cat = query.all()
    total_items = len(courses_cat)

    page = int(request.args.get("page", 1))
    items_per_page = 10
    start = (page - 1) * items_per_page
    end = start + items_per_page
    paginated_courses = courses_cat[start:end]

    titles = ["Course Name", "Department", "Number", "Add"]
    rows = [[
        render_template("catalog/course_info.html", course=c),
        c.dept,
        c.number,
        f'<button class="btn btn-primary">Enroll</button>'
    ] for c in paginated_courses]

    show_results = bool(subjectData or courseID or request.args.get("page"))

    total_pages = (total_items + items_per_page - 1) // items_per_page

    if request.headers.get("HX-Request"):
        if not show_results:
            return ""  
        return render_template("catalog/course_table.html", 
        titles=titles, 
        courses=paginated_courses,
        rows=rows, 
        term=term, 
        current_page=page, 
        total_pages=total_pages, 
        items_per_page=items_per_page, 
        total_items=total_items)


    return render_template(
        "enrollment.html",
        term=term,
        # titles=titles,
        # rows=rows,
        # courses=paginated_courses,
        # current_page=page,
        # total_pages=total_pages,
        # items_per_page=items_per_page,
        # total_items=total_items,
        # show_results=show_results
    )

def add_class():

    return None