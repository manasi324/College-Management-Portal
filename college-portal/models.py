from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Student(db.Model):
    __tablename__ = "student"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    course = db.Column(db.String(100))
    year = db.Column(db.String(10))
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    department = db.relationship('Department')
    
class Notice(db.Model):
    __tablename__ = "notice"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False) 
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    # Personal notices (e.g. attendance warnings) are targeted at a specific student
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    department = db.relationship('Department')
    author = db.relationship('User')
    student = db.relationship('Student')
    scope = db.Column(
        db.String(20),
        default="College"
    )

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)

class Material(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    link = db.Column(db.String(300), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    department = db.relationship('Department')
    author = db.relationship('User')

class Department(db.Model):
    __tablename__ = "departments"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    about = db.Column(db.Text)
    eligibility = db.Column(db.Text)
    syllabus = db.Column(db.Text)
    
class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False)

    department_id = db.Column(
        db.Integer,
        db.ForeignKey("departments.id")
    )

    department = db.relationship("Department")

    # ADD THESE
    hod = db.relationship("HOD", back_populates="user", uselist=False)
    teacher = db.relationship("Teacher", back_populates="user", uselist=False)

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer,db.ForeignKey("student.id"), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    student = db.relationship('Student')
    teacher = db.relationship('User')
    department = db.relationship('Department')


class Result(db.Model):
    __tablename__ = "results"

    id = db.Column(db.Integer, primary_key=True)

    student_id = db.Column(
        db.Integer,
        db.ForeignKey("student.id"),
        nullable=False
    )

    teacher_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    department_id = db.Column(
        db.Integer,
        db.ForeignKey("departments.id"),
        nullable=False
    )

    subject_id = db.Column(
        db.Integer,
        db.ForeignKey("subjects.id"),
        nullable=False
    )

    semester = db.Column(db.Integer)

    internal = db.Column(db.Integer, default=0)

    assignment = db.Column(db.Integer, default=0)

    external = db.Column(db.Integer, default=0)

    # NEW
    practical = db.Column(db.Integer, default=0)

    total = db.Column(db.Integer)

    grade = db.Column(db.String(5))

    status = db.Column(db.String(20))

    student = db.relationship("Student")
    teacher = db.relationship("User")
    department = db.relationship("Department")
    subject = db.relationship("Subject")

class Subject (db.Model):
    __tablename__ = "subjects"

    id = db.Column(db.Integer, primary_key=True)

    course = db.Column(db.String(100), nullable=False)

    semester = db.Column(db.Integer, nullable=False)

    subject_name = db.Column(db.String(200), nullable=False)

    department_id = db.Column(
        db.Integer,
        db.ForeignKey("departments.id"),
        nullable=False
    )

    department = db.relationship("Department")

class HOD(db.Model):
    __tablename__ = "hods"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        unique=True
    )

    department_id = db.Column(
        db.Integer,
        db.ForeignKey("departments.id"),
        nullable=False
    )

    user = db.relationship("User", back_populates="hod")
    department = db.relationship("Department")


class Teacher(db.Model):
    __tablename__ = "teachers"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        unique=True
    )

    department_id = db.Column(
        db.Integer,
        db.ForeignKey("departments.id"),
        nullable=False
    )

    user = db.relationship("User", back_populates="teacher")
    department = db.relationship("Department")