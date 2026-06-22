from flask import Flask, render_template, request, redirect
from config import Config
from models import db, Student

app = Flask(__name__)
app.config.from_object(Config)

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

        student = Student.query.filter_by(
            email=email,
            password=password
        ).first()

        if student:
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
    return render_template('dashboard.html')


@app.route('/logout')
def logout():
    return redirect('/')


if __name__ == '__main__':
 app.run(debug=True)