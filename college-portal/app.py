from flask import Flask, render_template, request, redirect, session, url_for
from config import Config
from models import db, Student, User, Department, Notice, Event, Material

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = "collegeportal"

db.init_app(app)

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


@app.route('/')
def home():
    return render_template('index.html')
@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        # Principal / HOD / Teacher
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
                session.clear()
                session["user_id"] = user.id
                session["role"] = "HOD"
                session["department"] = user.department.name
                session["department_id"] = user.department_id

                return redirect(url_for("hod_dashboard"))

            elif user.role == "Teacher":
                session.clear()
                session["user_id"] = user.id
                session["role"] = "Teacher"
                session["department"] = user.department.name
                session["department_id"] = user.department_id

                return redirect("/teacher_dashboard")

        # Student Login
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
                year=request.form['year']
            )

            db.session.add(student)

        else:

            department = Department.query.filter_by(
                name=request.form['department']
            ).first()

            user = User(
                name=request.form['name'],
                email=request.form['email'],
                password=request.form['password'],
                role=role,
                department_id=department.id
            )

            db.session.add(user)

        db.session.commit()

        return redirect('/login')

    return render_template('register.html')

@app.route('/dashboard')
def dashboard():

    if 'student_id' not in session:
        return redirect('/login')

    student = Student.query.get(session['student_id'])

    return render_template(
        'dashboard.html',
        student=student
    )
@app.route('/profile')
def profile():
    student = Student.query.get(session['student_id'])
    return render_template('profile.html', student=student)

@app.route('/notices')
def notices():
    notices = Notice.query.all()
    return render_template('notices.html', notices=notices)

@app.route('/events')
def events():
    events = Event.query.all()
    return render_template('events.html', events=events)

@app.route('/materials')
def materials():
    materials = Material.query.all()
    return render_template('materials.html', materials=materials)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

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


@app.route('/admin_dashboard')
def admin_dashboard():

    if not session.get('admin'):
        return redirect('/login')

    total_students = Student.query.count()
    total_notices = 0
    total_events = 0

    return render_template(
        'admin_dashboard.html',
        total_students=total_students,
        total_notices=total_notices,
        total_events=total_events
    )

@app.route('/students')
def students():
    if session.get("role") != "Principal":
        return redirect("/login")
    students = Student.query.all()
    return render_template('students.html', students=students)



@app.route('/delete_student/<int:id>')
def delete_student(id):
    student = Student.query.get_or_404(id)
    db.session.delete(student)
    db.session.commit()
    return redirect('/students')

@app.route('/edit_student/<int:id>', methods=['GET', 'POST'])
def edit_student(id):
    student = Student.query.get_or_404(id)

    if request.method == 'POST':
        student.name = request.form['name']
        student.email = request.form['email']
        student.course = request.form['course']
        student.year = request.form['year']

        db.session.commit()
        return redirect('/students')

    return render_template('edit_student.html', student=student)
    
@app.route('/manage_notices', methods=['GET', 'POST'])
def manage_notices():

    # Principal only
    if session.get("role") != "Principal":
        return redirect('/login')

    if request.method == 'POST':
        notice = Notice(
            title=request.form['title'],
            description=request.form['description']
        )

        db.session.add(notice)
        db.session.commit()

        return redirect('/manage_notices')

    notices = Notice.query.all()
    return render_template('manage_notices.html', notices=notices)

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
    return render_template('edit_student.html', student=student)

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

@app.route('/principal_dashboard')
def principal_dashboard():
    if session.get("role") != "Principal":
        return redirect("/login")
    return render_template('principal_dashboard.html')



@app.route("/hod_dashboard")
def hod_dashboard():

    if session.get("role") != "HOD":
        return redirect("/login")

    hod = User.query.get(session["user_id"])

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

@app.route('/manage_hods')
def manage_hods():

    if session.get("role") != "Principal":
        return redirect('/login')

    hods = User.query.filter_by(role="HOD").all()

    return render_template(
        'manage_hods.html',
        hods=hods
    )
@app.route("/hod_students")
def hod_students():
    return "<h2>Manage Students - Coming Soon</h2>"


@app.route("/hod_teachers")
def hod_teachers():
    return "<h2>Manage Teachers - Coming Soon</h2>"


@app.route("/department_notices")
def department_notices():
    return "<h2>Department Notices - Coming Soon</h2>"


@app.route("/study_materials")
def study_materials():
    return "<h2>Study Materials - Coming Soon</h2>"


@app.route("/attendance")
def attendance():
    return "<h2>Attendance - Coming Soon</h2>"


@app.route("/assignments")
def assignments():
    return "<h2>Assignments - Coming Soon</h2>"


@app.route("/marks")
def marks():
    return "<h2>Internal Marks - Coming Soon</h2>"

@app.route("/teacher_students")
def teacher_students():

    if session.get("role") != "Teacher":
        return redirect("/login")

    teacher = User.query.get(session["user_id"])

    students = Student.query.filter_by(
        department_id=teacher.department_id
    ).all()

    return render_template(
        "teacher_students.html",
        students=students
    )

@app.route("/upload_material")
def upload_material():

    if session.get("role") != "Teacher":
        return redirect("/login")

    return render_template("upload_material.html")
@app.route("/teacher_notices")
def teacher_notices():

    if session.get("role") != "Teacher":
        return redirect("/login")

    notices = Notice.query.all()

    return render_template(
        "teacher_notices.html",
        notices=notices
    )
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)