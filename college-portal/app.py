from flask import Flask, render_template, request, redirect, session
from config import Config
from models import db, Student

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = "collegeportal"

db.init_app(app)

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

        # Admin Login
        if email == "admin@college.com" and password == "admin123":
            session.clear()
            session['admin'] = True
            return redirect('/admin_dashboard')

        # Student Login
        student = Student.query.filter_by(
            email=email,
            password=password
        ).first()

        if student:
            session.clear()
            session['student_id'] = student.id
            return redirect('/dashboard')

        return render_template(
            'login.html',
            error="Invalid Email or Password"
        )

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        student = Student(
            name=request.form['name'],
            email=request.form['email'],
            password=request.form['password'],
            course=request.form['course'],
            year=request.form['year']
        )

        db.session.add(student)
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
    return render_template('notices.html')

@app.route('/events')
def events():
    return render_template('events.html')

@app.route('/materials')
def materials():
    return render_template('materials.html')

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
        return redirect('/admin')

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
    students = Student.query.all()
    return render_template('students.html', students=students)
 

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)