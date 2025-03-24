from flask import Blueprint, render_template
from flask_login import login_required

site_enrollment = Blueprint("site_enrollment", __name__)

@site_enrollment.route("/Test")
def test():
    return 404

@site_enrollment.route("/")
def enrollment():
    # Options are
    #   - see enrolled classes (select term)
    #   - see available classes (select term)
    #       - includes # of enrolled students
    #       - includes available seats, waitlist slots
    #   - go to enrollment tool
    return 404

@site_enrollment.route("/classes")
@login_required
def classes():
    # just a page with links to different
    # site_enrollment.classes_term endpoints
    # maybe use a dropdown; maybe use a carousel; idk
    return 404

@site_enrollment.route("/classes/<string:term>")
@login_required
def classes_term(term):
    # returns a calendar displaying term schedule
    #   - contains class schedule + lectures
    #   - ability to download for input into Google
    #       Calendare, etc. would be nice
    # also returns a list of enrolled classes
    # has link to enroll in courses for this term
    return 404

@site_enrollment.route("/catalog")
def catalog(term):
    # just a page with links to different
    # site_enrollment.catalog_term endpoints
    # maybe use a dropdown; maybe use a carousel; idk
    return 404

@site_enrollment.route("/catalog/<string:term>")
def catalog_term(term):
    # returns a list of courses offered
    #   - includes course name, ID, CRN, etc.
    #   - includes instructorm TAs
    #   - includes Dates/Times of classes, exams
    #       - hovercard w/ calendar element would be neat
    #   - includes level of enrollment, waitlist availability
    return 404

@site_enrollment.route("/enroll")
@login_required
def enroll():
    # just a page with links to different
    # site_enrollment.enroll_term endpoints
    # maybe use a carousel; maybe use a dropdown; idk
    return 404

@site_enrollment.route("/enroll/<string:term>")
@login_required
def enroll_term(term):
    # likely includes reuised components from
    # `catalog_term` and `classes_term` pages
    # has a course catalog and calendar of selected term
    # checks enrollment availability before allowing db changes
    # maybe include prerequisites/restrictions
    return 404