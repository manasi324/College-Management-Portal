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

        print("Email:", email)
        print("Password:", password)

        student = Student.query.filter_by(email=email).first()

        print("Student:", student)

        if student:
            print("DB Password:", student.password)

            if student.password == password:
                session['student_id'] = student.id
                return redirect('/dashboard')

        return "Invalid Email or Password"

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


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)