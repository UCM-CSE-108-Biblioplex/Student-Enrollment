from flask_login import UserMixin
from . import db
import time  # useful later for potential API Keys

class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    is_admin = db.Column(db.Boolean, default=False)
    first_name = db.Column(db.String(255), nullable=False)
    middle_name = db.Column(db.String(255), nullable=True)
    last_name = db.Column(db.String(255), nullable=True)
    username = db.Column(db.String(255), unique=True, nullable=False, info={"min_length": 2})
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False, info={"min_length": 4})
    api_keys = db.relationship("APIKey", backref="user")

    courses = db.relationship(
        "Course",
        secondary= "roles",
        back_populates="users",
        primaryjoin="User.id == roles.c.user_id",
        secondaryjoin="Course.id == roles.c.course_id"
    )
    roles = db.relationship(
        "Role",
        secondary="roles",
        backref="users"
    )

    def to_dict(self):
        return({attr.name: getattr(self, attr.name) for attr in self.__table__.columns})

    def is_instructor(self):
        return(any(role.name == "Instructor" for role in self.roles))

    def get_role_assignments(self):
        assignments = db.session.query(
            Course, Role
        ).join(
            roles, Course.id == roles.c.course_id
        ).join(
            Role, Role.id == roles.c.role_id
        ).filter(
            roles.c.user_id == self.id
        ).order_by(Course.term, Course.dept, Course.number).all()
        return(assignments)

    def get_courses_role(self, role, page=1, per_page=50):
        courses_with_role = db.session.query(
            Course
        ).join(
            roles
        ).filter(
            roles.c.user_id == self.id
        ).filter(
            roles.c.role_id == role.id
        ).paginate(page=page, per_page=per_page)
        return(courses_with_role)

class APIKey(db.Model):
    __tablename__ = "keys"
    id = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.Integer, db.ForeignKey("users.id"))
    is_admin = db.Column(db.Boolean, default=False)
    key = db.Column(db.String(255), nullable=False)
    expiry = db.Column(db.Integer, nullable=False)

class Course(db.Model):
    __tablename__ = "courses"
    id = db.Column(db.Integer, primary_key=True)
    term = db.Column(db.String(7), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    dept = db.Column(db.String(7), nullable=False)
    number = db.Column(db.String(7), nullable=False)
    session = db.Column(db.String(7), nullable=False)
    units = db.Column(db.Integer, nullable=False)
    maximum = db.Column(db.Integer)

    users = db.relationship(
        "User", secondary="roles", back_populates="courses"
    )

    schedules = db.relationship("Schedule", backref="course")

    prerequisites = db.relationship("CoursePrerequisite", backref="course")
    corequisites = db.relationship("CourseCorequisite", backref="course")

    def get_students_with_grades(self, page=1, per_page=50):
        """
        Fetches paginated students enrolled in this course along with their grades.
        Returns a SQLAlchemy Pagination object.
        """
        student_role = Role.query.filter_by(name="Student").first()
        if not student_role:
            return None # Or raise an error

        # Select User objects and the grade from the roles table
        query = db.session.query(
            User, roles.c.grade
        ).join(
            roles, User.id == roles.c.user_id
        ).filter(
            roles.c.course_id == self.id,
            roles.c.role_id == student_role.id
        ).order_by(User.last_name, User.first_name)

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        return pagination

    def to_dict(self):
        return({attr.name: getattr(self, attr.name) for attr in self.__table__.columns})

class CoursePrerequisite(db.Model):
    __tablename__ = "prerequisites"
    id = db.Column(db.Integer, primary_key=True)
    courseid = db.Column(db.Integer, db.ForeignKey("courses.id"))
    dept = db.Column(db.String(7), nullable=False)
    number = db.Column(db.String(7), nullable=False)

    def to_dict(self):
        return({"dept": self.dept, "number": self.number})

class CourseCorequisite(db.Model):
    __tablename__ = "corequisites"
    id = db.Column(db.Integer, primary_key=True)
    courseid = db.Column(db.Integer, db.ForeignKey("courses.id"))
    dept = db.Column(db.String(7), nullable=False)
    number = db.Column(db.String(7), nullable=False)

    def to_dict(self):
        return({"dept": self.dept, "number": self.number})

class Department(db.Model):
    __tablename__ = "departments"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    abbreviation = db.Column(db.String(7))

    def to_dict(self):
        return({attr.name: getattr(self, attr.name) for attr in self.__table__.columns})

class Term (db.Model):
    __tablename__ = "terms"
    id = db.Column(db.Integer, primary_key=True)
    index = db.Column(db.Integer, unique=True)
    name = db.Column(db.String(255))
    abbreviation = db.Column(db.String(7))

    def to_dict(self):
        return({attr.name: getattr(self, attr.name) for attr in self.__table__.columns})

class Schedule(db.Model):
    __tablename__ = "schedules"
    id=db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"))
    schedule_type = db.Column(db.String(31), nullable=False)
    
    sunday = db.Column(db.Boolean)
    monday = db.Column(db.Boolean)
    tuesday = db.Column(db.Boolean)
    wednesday = db.Column(db.Boolean)
    thursday = db.Column(db.Boolean)
    friday = db.Column(db.Boolean)
    saturday = db.Column(db.Boolean)
    
    start_time = db.Column(db.Integer) # in minutes
    end_time = db.Column(db.Integer)

    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)

class Role(db.Model):
    __tablename__ = "roles_def"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(63), nullable=False)

    def to_dict(self):
        return({"id": self.id, "name": self.name})

roles = db.Table(
    "roles",
    db.metadata,
    db.Column("user_id", db.Integer, db.ForeignKey("users.id"), primary_key=True),
    db.Column("course_id", db.Integer, db.ForeignKey("courses.id"), primary_key=True),
    db.Column("role_id", db.Integer, db.ForeignKey("roles_def.id")),
    db.Column("grade", db.String(10), nullable=True)
)