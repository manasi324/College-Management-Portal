from flask import Flask, render_template, request, redirect, session, url_for
from config import Config
from models import db, Student, User, Department, Teacher, HOD, Notice, Event, Material, Attendance, Mark
from datetime import date
from flask import flash
app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = "collegeportal"

db.init_app(app)
print(app.config["SQLALCHEMY_DATABASE_URI"])

with app.app_context():

    db.create_all()
    print("✅ Database connected successfully!")

    departments = [
        "BSC CS & IT",
        "BCOM",
        "BAF",
        "BMS",
        "BAMMC"
    ]

    for dept in departments:
        if not Department.query.filter_by(name=dept).first():
            db.session.add(Department(name=dept))

    if not User.query.filter_by(email="principal@college.com").first():
        principal = User(
            name="Principal",
            email="principal@college.com",
            password="principal123",
            role="Principal"
        )
        db.session.add(principal)

    db.session.commit()

with app.app_context():
    db.create_all()


# ==================== HOME ====================

@app.route('/')
def home():
    return render_template('index.html')


# ==================== AUTHENTICATION ====================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Check Principal / HOD / Teacher
        user = User.query.filter_by(
            email=email,
            password=password
        ).first()

        if user:
            session.clear()

            if user.role == "Principal":
                session["role"] = "Principal"
                return redirect("/principal_dashboard")

            elif user.role == "HOD":
                session["user_id"] = user.id
                session["role"] = "HOD"
                session["department"] = user.department.name
                session["department_id"] = user.department_id
                return redirect(url_for("hod_dashboard"))

            elif user.role == "Teacher":
                session["user_id"] = user.id
                session["role"] = "Teacher"
                session["department"] = user.department.name
                session["department_id"] = user.department_id
                return redirect("/teacher_dashboard")

        # Check Student Login
        student = Student.query.filter_by(
            email=email,
            password=password
        ).first()

        if student:
            session.clear()
            session["student_id"] = student.id
            return redirect("/dashboard")

        return render_template(
            "login.html",
            error="Invalid Email or Password"
        )

    return render_template("login.html")

@app.route("/logout")
def logout():

    # Remove all session data
    session.clear()

    # Redirect to login page
    return redirect("/login")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        role = request.form['role']

        if role == "Student":
            student = Student(
                name=request.form['name'],
                email=request.form['email'],
                password=request.form['password'],
                course=request.form['course'],
                year=request.form['year'],
                department_id=Department.query.filter_by(
                    name=request.form['department']
                ).first().id
            )

            db.session.add(student)

        elif role == "HOD":

            department = Department.query.filter_by(
                name=request.form['department']
            ).first()

            if User.query.filter_by(email=request.form['email']).first():
                departments = Department.query.all()
                return render_template(
                    'register.html',
                    departments=departments,
                    error="Email already registered"
                )

            user = User(
                name=request.form['name'],
                email=request.form['email'],
                password=request.form['password'],
                role="HOD",
                department_id=department.id
            )

            db.session.add(user)
            db.session.flush()

            hod = HOD(
                user_id=user.id,
                department_id=department.id
            )

            db.session.add(hod)

        else:   # Teacher

            department = Department.query.filter_by(
                name=request.form['department']
            ).first()

            user = User(
                name=request.form['name'],
                email=request.form['email'],
                password=request.form['password'],
                role="Teacher",
                department_id=department.id
            )

            db.session.add(user)
            db.session.flush()

            teacher = Teacher(
                user_id=user.id,
                department_id=department.id
            )

            db.session.add(teacher)

        db.session.commit()

        return redirect('/login')

    departments = Department.query.all()
    return render_template('register.html', departments=departments)


# ==================== STUDENT ROUTES ====================

@app.route('/dashboard')
def dashboard():
    if 'student_id' not in session:
        return redirect('/login')

    student = Student.query.get(session['student_id'])

    print("✅ LOADING dashboard.html")

    return render_template('dashboard.html', student=student)


@app.route('/profile')
def profile():
    if 'student_id' not in session:
        return redirect('/login')
    student = Student.query.get(session['student_id'])
    return render_template('profile.html', student=student)


@app.route('/student/notices')
def student_notices():
    if 'student_id' not in session:
        return redirect('/login')
    notices = Notice.query.all()
    return render_template('notices.html', notices=notices)


@app.route('/student/events')
def student_events():
    if 'student_id' not in session:
        return redirect('/login')
    events = Event.query.all()
    return render_template('events.html', events=events)



@app.route("/student_materials")
def student_materials():

    if 'student_id' not in session:
        return redirect('/login')

    student = Student.query.get(session['student_id'])

    materials = Material.query.filter_by(
        department_id=student.department_id
    ).all()

    return render_template(
        "student_materials.html",
        student=student,
        materials=materials
    )

@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    student = Student.query.get(session['student_id'])

    if request.method == 'POST':
        student.name = request.form['name']
        student.email = request.form['email']
        student.course = request.form['course']
        student.year = request.form['year']
        db.session.commit()
        return redirect('/profile')

    return render_template('edit_profile.html', student=student)


# ==================== PRINCIPAL ROUTES ====================

@app.route('/principal_dashboard')
def principal_dashboard():
    if session.get("role") != "Principal":
        return redirect("/login")
    return render_template('principal_dashboard.html')


@app.route('/students')
def students():
    if session.get("role") != "Principal":
        return redirect("/login")
    students_list = Student.query.all()
    return render_template('students.html', students=students_list)


@app.route('/delete_student/<int:id>')
def delete_student(id):
    student = Student.query.get_or_404(id)

    # Check user role
    if session.get("role") == "Principal":
        pass

    elif session.get("role") == "HOD":
        if student.department_id != session.get("department_id"):
            return "Access Denied", 403

    else:
        return redirect("/login")

    db.session.delete(student)
    db.session.commit()

    if session.get("role") == "Principal":
        return redirect("/students")
    else:
        return redirect("/hod_students")


@app.route('/edit_student/<int:id>', methods=['GET', 'POST'])
def edit_student(id):
    student = Student.query.get_or_404(id)

    # Check user role
    if session.get("role") == "Principal":
        pass

    elif session.get("role") == "HOD":
        if student.department_id != session.get("department_id"):
            return "Access Denied", 403

    else:
        return redirect("/login")

    if request.method == "POST":
        student.name = request.form["name"]
        student.email = request.form["email"]
        student.course = request.form["course"]
        student.year = request.form["year"]

        db.session.commit()

        if session.get("role") == "Principal":
            return redirect("/students")
        else:
            return redirect("/hod_students")

    if session.get("role") == "Principal":
         back_url = url_for("students")
    else:
      back_url = url_for("hod_students")

    return render_template(
    "edit_student.html",
    student=student,
    back_url=back_url
)


@app.route('/manage_notices', methods=['GET', 'POST'])
def manage_notices():

    if session.get("role") != "Principal":
        return redirect("/login")

    principal = User.query.get(session["user_id"])

    if request.method == "POST":

        notice = Notice(
            title=request.form["title"],
            description=request.form["description"],
            scope="College",          # Principal notices are for everyone
            department_id=None,       # No department
            created_by=principal.id
        )

        db.session.add(notice)
        db.session.commit()

        flash("Notice added successfully!", "success")

        return redirect("/manage_notices")

    notices = Notice.query.filter_by(
        scope="College"
    ).all()

    return render_template(
        "manage_notices.html",
        notices=notices
    )


@app.route('/edit_notice/<int:id>', methods=['GET', 'POST'])
def edit_notice(id):

    if session.get("role") != "Principal":
        return redirect("/login")

    notice = Notice.query.get_or_404(id)

    if request.method == "POST":

        notice.title = request.form["title"]
        notice.description = request.form["description"]

        db.session.commit()

        flash("Notice updated successfully!", "success")

        return redirect("/manage_notices")

    return render_template(
        "edit_notice.html",
        notice=notice
    )


@app.route('/delete_notice/<int:id>')
def delete_notice(id):

    if session.get("role") != "Principal":
        return redirect("/login")

    notice = Notice.query.get_or_404(id)

    db.session.delete(notice)
    db.session.commit()

    flash("Notice deleted successfully!", "success")

    return redirect("/manage_notices")

@app.route('/manage_events', methods=['GET', 'POST'])
def manage_events():
    if session.get("role") != "Principal":
        return redirect("/login")
    
    if request.method == 'POST':
        event = Event(
            title=request.form['title'],
            date=request.form['date'],
            description=request.form['description']
        )
        db.session.add(event)
        db.session.commit()
        return redirect('/manage_events')

    events = Event.query.all()
    return render_template('manage_events.html', events=events)


@app.route('/edit_event/<int:id>', methods=['GET', 'POST'])
def edit_event(id):
    if session.get("role") != "Principal":
        return redirect("/login")

    event = Event.query.get_or_404(id)

    if request.method == "POST":
        event.title = request.form["title"]
        event.date = request.form["date"]
        event.description = request.form["description"]
        db.session.commit()
        return redirect("/manage_events")

    return render_template("edit_event.html", event=event)


@app.route('/delete_event/<int:id>')
def delete_event(id):
    if session.get("role") != "Principal":
        return redirect("/login")

    event = Event.query.get_or_404(id)
    db.session.delete(event)
    db.session.commit()
    return redirect("/manage_events")


@app.route('/manage_materials', methods=['GET', 'POST'])
def manage_materials():
    if session.get("role") != "Principal":
        return redirect("/login")

    if request.method == 'POST':
        material = Material(
            subject=request.form['subject'],
            title=request.form['title'],
            link=request.form['link']
        )
        db.session.add(material)
        db.session.commit()
        return redirect('/manage_materials')

    materials = Material.query.all()
    return render_template('manage_materials.html', materials=materials)


@app.route('/manage_hods')
def manage_hods():
    if session.get("role") != "Principal":
        return redirect('/login')

    hods = User.query.filter_by(role="HOD").all()
    return render_template('manage_hods.html', hods=hods)


@app.route('/add_hod', methods=['GET', 'POST'])
def add_hod():
    if session.get("role") != "Principal":
        return redirect("/login")
    
    if request.method == "POST":
        department = Department.query.filter_by(name=request.form["department"]).first()
        hod = User(
            name=request.form["name"],
            email=request.form["email"],
            password=request.form["password"],
            role="HOD",
            department_id=department.id
        )
        db.session.add(hod)
        db.session.commit()
        return redirect("/manage_hods")
    
    departments = Department.query.all()
    return render_template("add_hod.html", departments=departments)


@app.route('/edit_hod/<int:id>', methods=['GET', 'POST'])
def edit_hod(id):
    if session.get("role") != "Principal":
        return redirect("/login")
    
    hod = User.query.get_or_404(id)
    
    if request.method == "POST":
        hod.name = request.form["name"]
        hod.email = request.form["email"]
        hod.password = request.form["password"]
        department = Department.query.filter_by(name=request.form["department"]).first()
        hod.department_id = department.id
        db.session.commit()
        return redirect("/manage_hods")
    
    departments = Department.query.all()
    return render_template("edit_hod.html", hod=hod, departments=departments)


@app.route('/delete_hod/<int:id>')
def delete_hod(id):
    if session.get("role") != "Principal":
        return redirect("/login")
    
    hod = User.query.get_or_404(id)
    db.session.delete(hod)
    db.session.commit()
    return redirect("/manage_hods")


@app.route('/manage_teachers')
def manage_teachers():
    if session.get("role") != "Principal":
        return redirect("/login")

    teachers = User.query.filter_by(role="Teacher").all()
    return render_template("manage_teachers.html", teachers=teachers)


@app.route('/add_teacher', methods=['GET', 'POST'])
def add_teacher():
    if session.get("role") != "Principal":
        return redirect("/login")

    if request.method == "POST":
        department = Department.query.filter_by(
            name=request.form["department"]
        ).first()

        teacher = User(
            name=request.form["name"],
            email=request.form["email"],
            password=request.form["password"],
            role="Teacher",
            department_id=department.id
        )

        db.session.add(teacher)
        db.session.commit()
        return redirect("/manage_teachers")

    departments = Department.query.all()
    return render_template("add_teacher.html", departments=departments)


@app.route("/edit_teacher/<int:id>", methods=["GET", "POST"])
def edit_teacher(id):

    if session.get("role") not in ["Principal", "HOD"]:
        return redirect("/login")

    teacher = User.query.get_or_404(id)

    # HOD can edit only teachers from their own department
    if session.get("role") == "HOD":
        if teacher.department_id != session["department_id"]:
            return "Access Denied", 403

    if request.method == "POST":
        teacher.name = request.form["name"]
        teacher.email = request.form["email"]
        teacher.password = request.form["password"]

        department = Department.query.filter_by(
            name=request.form["department"]
        ).first()

        teacher.department_id = department.id

        # Also update the teachers table
        teacher_record = Teacher.query.filter_by(user_id=teacher.id).first()
        if teacher_record:
            teacher_record.department_id = department.id

        db.session.commit()

        if session.get("role") == "Principal":
            return redirect("/manage_teachers")
        else:
            return redirect("/hod_teachers")

    departments = Department.query.all()

    return render_template(
        "edit_teacher.html",
        teacher=teacher,
        departments=departments
    )


@app.route("/delete_teacher/<int:id>")
def delete_teacher(id):

    if session.get("role") not in ["Principal", "HOD"]:
        return redirect("/login")

    teacher = User.query.get_or_404(id)

    # HOD can delete only teachers from their own department
    if session.get("role") == "HOD":
        if teacher.department_id != session["department_id"]:
            return "Access Denied", 403

    # Delete from teachers table first
    teacher_record = Teacher.query.filter_by(user_id=id).first()
    if teacher_record:
        db.session.delete(teacher_record)

    # Delete from users table
    db.session.delete(teacher)

    db.session.commit()

    if session.get("role") == "Principal":
        return redirect("/manage_teachers")
    else:
        return redirect("/hod_teachers")


# ==================== HOD DASHBOARD ====================

@app.route("/hod_dashboard")
def hod_dashboard():
    if session.get("role") != "HOD":
        return redirect("/login")

    hod = User.query.get(session["user_id"])
      
    return render_template(
        "hod_dashboard.html",
        hod=hod
    )

    total_students = Student.query.filter_by(
        department_id=hod.department_id
    ).count()

    total_teachers = User.query.filter_by(
        role="Teacher",
        department_id=hod.department_id
    ).count()

    total_notices = Notice.query.count()
    total_materials = Material.query.count()

    return render_template(
        "hod_dashboard.html",
        hod=hod,
        total_students=total_students,
        total_teachers=total_teachers,
        total_notices=total_notices,
        total_materials=total_materials
    )


@app.route("/hod_students")
def hod_students():
    if session.get("role") != "HOD":
        return redirect("/login")

    students = Student.query.filter_by(
        department_id=session["department_id"]
    ).all()

    return render_template(
        "hod_students.html",
        students=students
    )

@app.route("/hod_teachers")
def hod_teachers():
    if session.get("role") != "HOD":
        return redirect("/login")

    department_id = session["department_id"]

    teachers = (
        Teacher.query
        .filter_by(department_id=department_id)
        .all()
    )

    return render_template(
        "hod_teachers.html",
        teachers=teachers
    )

@app.route("/department_notices")
def department_notices():
    return "<h2>Department Notices - Coming Soon</h2>"


@app.route("/study_materials")
def study_materials():

    if session.get("role") != "Teacher":
        return redirect("/login")

    teacher = User.query.get(session["user_id"])

    materials = Material.query.filter_by(
        department_id=teacher.department_id
    ).all()

    return render_template(
        "study_materials.html",
        materials=materials
    )
@app.route("/department_attendance")
def department_attendance():

    if session.get("role") != "HOD":
        return redirect("/login")

    department_id = session["department_id"]

    students = Student.query.filter_by(
        department_id=department_id
    ).all()

    attendance_data = []

    for student in students:

        total = Attendance.query.filter_by(
            student_id=student.id
        ).count()

        present = Attendance.query.filter_by(
            student_id=student.id,
            status="Present"
        ).count()

        percentage = 0

        if total > 0:
            percentage = round((present / total) * 100, 2)

        attendance_data.append({
            "student": student,
            "total": total,
            "present": present,
            "percentage": percentage
        })

    # Summary cards
    total_students = len(attendance_data)

    average_attendance = 0
    if total_students > 0:
        average_attendance = round(
            sum(s["percentage"] for s in attendance_data) / total_students,
            2
        )

    below_75 = sum(
        1 for s in attendance_data
        if s["percentage"] < 75
    )

    today = str(date.today())

    today_attendance = Attendance.query.filter_by(
        department_id=department_id,
        date=today
    ).count()

    # Pie chart data
    present_count = Attendance.query.filter_by(
        department_id=department_id,
        status="Present"
    ).count()

    absent_count = Attendance.query.filter_by(
        department_id=department_id,
        status="Absent"
    ).count()

    return render_template(
        "department_attendance.html",
        attendance_data=attendance_data,
        total_students=total_students,
        average_attendance=average_attendance,
        below_75=below_75,
        today_attendance=today_attendance,
        present_count=present_count,
        absent_count=absent_count
    )

@app.route("/send_warning/<int:student_id>")
def send_warning(student_id):

    if session.get("role") != "HOD":
        return redirect("/login")

    student = Student.query.get_or_404(student_id)

    total = Attendance.query.filter_by(
        student_id=student.id
    ).count()

    present = Attendance.query.filter_by(
        student_id=student.id,
        status="Present"
    ).count()

    percentage = 0

    if total > 0:
        percentage = round((present / total) * 100, 2)

    notice = Notice(
        title="Attendance Warning",
        description=f"Your attendance is only {percentage}%. Please improve your attendance immediately to avoid disciplinary action.",
        department_id=student.department_id,
        created_by=session["user_id"]
    )

    db.session.add(notice)
    db.session.commit()

    flash("Warning notice sent successfully!", "success")

    return redirect("/department_attendance")

@app.route("/assignments")
def assignments():
    return "<h2>Assignments - Coming Soon</h2>"


@app.route("/marks")
def marks():
    return "<h2>Internal Marks - Coming Soon</h2>"


# ==================== TEACHER DASHBOARD ====================

@app.route("/teacher_dashboard")
def teacher_dashboard():
    if session.get("role") != "Teacher":
        return redirect("/login")

    teacher = User.query.get(session["user_id"])

    total_students = Student.query.filter_by(
        department_id=teacher.department_id
    ).count()

    total_materials = Material.query.count()
    total_notices = Notice.query.count()
    total_events = Event.query.count()

    return render_template(
        "teacher_dashboard.html",
        teacher=teacher,
        total_students=total_students,
        total_materials=total_materials,
        total_notices=total_notices,
        total_events=total_events
    )


@app.route("/teacher_students")
def teacher_students():

    if session.get("role") != "Teacher":
        return redirect("/login")

    teacher = User.query.get(session["user_id"])

    students = Student.query.filter_by(
        department_id=teacher.department_id
    ).all()

    return render_template(
        "hod_students.html",
        students=students
    )


@app.route("/upload_material", methods=["GET", "POST"])
def upload_material():

    if session.get("role") != "Teacher":
        return redirect("/login")

    teacher = User.query.get(session["user_id"])

    if request.method == "POST":

        material = Material(
            subject=request.form["subject"],
            title=request.form["title"],
            link=request.form["link"],
            department_id=teacher.department_id,
            created_by=teacher.id
        )

        db.session.add(material)
        db.session.commit()

        flash("Study Material Uploaded Successfully!", "success")

        return redirect("/study_materials")

    return render_template("upload_material.html")

@app.route("/edit_material/<int:id>", methods=["GET", "POST"])
def edit_material(id):

    if session.get("role") != "Teacher":
        return redirect("/login")

    teacher = User.query.get(session["user_id"])

    material = Material.query.get_or_404(id)

    # Teacher can edit only their department's materials
    if material.department_id != teacher.department_id:
        return "Access Denied", 403

    if request.method == "POST":

        material.subject = request.form["subject"]
        material.title = request.form["title"]
        material.link = request.form["link"]

        db.session.commit()

        flash("Material updated successfully!", "success")

        return redirect("/study_materials")

    return render_template(
        "edit_material.html",
        material=material
    )

@app.route("/teacher_notices")
def teacher_notices():
    if session.get("role") != "Teacher":
        return redirect("/login")

    notices = Notice.query.all()
    return render_template(
        "teacher_notices.html",
        notices=notices
    )

@app.route("/attendance", methods=["GET", "POST"])
def attendance():

    if session.get("role") != "Teacher":
        return redirect("/login")

    teacher = User.query.get(session["user_id"])

    students = Student.query.filter_by(
        department_id=teacher.department_id
    ).all()

    if request.method == "POST":

        today = str(date.today())

        for student in students:

            status = request.form.get(f"status_{student.id}")

            existing = Attendance.query.filter_by(
                student_id=student.id,
                date=today
            ).first()

            if existing:
                existing.status = status
                existing.teacher_id = teacher.id
                existing.department_id = teacher.department_id

            else:
                attendance = Attendance(
                    student_id=student.id,
                    teacher_id=teacher.id,
                    department_id=teacher.department_id,
                    date=today,
                    status=status
                )

                db.session.add(attendance)

        db.session.commit()

        flash("Attendance saved successfully!", "success")

        return redirect("/attendance")

    return render_template(
        "attendance.html",
        students=students,
        teacher=teacher,
        today=date.today()
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
