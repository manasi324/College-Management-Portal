from flask import (Flask, render_template, request, redirect, session, url_for, jsonify)
from config import Config
from models import (db,Student,User,Department,Teacher,HOD,Notice,Event,Material,Attendance,Result,Subject)
from flask import flash
from datetime import date
from reportlab.platypus import ( SimpleDocTemplate,Table,TableStyle,Paragraph,Spacer )
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER
from flask import send_file
import io
import os
from datetime import datetime
from reportlab.platypus import Image
import qrcode
import tempfile
from reportlab.platypus import HRFlowable
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image as PILImage
from PIL import ImageDraw as PILDraw
from PIL import ImageFont as PILFont
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

# Safe migration: add notice.student_id column (for personal warnings) if missing
with app.app_context():
    try:
        from sqlalchemy import text
        db.session.execute(text("ALTER TABLE notice ADD COLUMN student_id INT"))
        db.session.commit()
        print("✅ Added notice.student_id column (personal warnings)")
    except Exception:
        db.session.rollback()


# ==================== HOME ====================

@app.route("/")
def home():

    departments = Department.query.all()

    principal_notices = Notice.query.filter_by(
        scope="College"
    ).order_by(Notice.id.desc()).all()

    events = Event.query.order_by(
        Event.id.desc()
    ).all()

    return render_template(
        "public/index.html",
        departments=departments,
        principal_notices=principal_notices,
        events=events
    )



# ==================== AUTHENTICATION ====================

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        # Principal / HOD / Teacher Login
        user = User.query.filter_by(
            email=email,
            password=password
        ).first()

        if user:

            print("User found:", user.email, user.role, user.id)

            session.clear()

            session["user_id"] = user.id
            session["role"] = user.role
            session["department_id"] = user.department_id

            if user.department:
                session["department"] = user.department.name

            print("Session after login:", dict(session))

            if user.role == "Principal":
                return redirect("/principal_dashboard")

            elif user.role == "HOD":
                return redirect("/hod_dashboard")

            elif user.role == "Teacher":
                return redirect("/teacher_dashboard")

        # Student Login
        student = Student.query.filter_by(
            email=email,
            password=password
        ).first()

        if student:

            session.clear()

            session["student_id"] = student.id
            session["role"] = "Student"

            return redirect("/dashboard")

        return render_template(
            "public/login.html",
            error="Invalid Email or Password"
        )

    return render_template("public/login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully!", "success")
    return redirect("/login")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        role = request.form['role']
        email = request.form['email']
        password = request.form['password']

        departments = Department.query.all()

        # ----- Duplicate check: email must be unique across User + Student -----
        duplicate_error = None

        if User.query.filter_by(email=email).first():
            duplicate_error = "This email is already registered. Please use a different email or login."

        if not duplicate_error and Student.query.filter_by(email=email).first():
            duplicate_error = "This email is already registered as a student. Please use a different email or login."

        if duplicate_error:
            return render_template(
                'public/register.html',
                departments=departments,
                error=duplicate_error
            )

        if role == "Student":
            student = Student(
                name=request.form['name'],
                email=email,
                password=password,
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

            user = User(
                name=request.form['name'],
                email=email,
                password=password,
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
                email=email,
                password=password,
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

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            return render_template(
                'public/register.html',
                departments=departments,
                error="Registration failed. That email or details may already exist."
            )

        return redirect('/login')

    departments = Department.query.all()
    return render_template('public/register.html', departments=departments)


# ==================== STUDENT ROUTES ====================

@app.route('/dashboard')
def dashboard():
    if 'student_id' not in session:
        return redirect('/login')

    student = Student.query.get(session['student_id'])
    cga = calculate_cgpa(student.id)
    sgpa_data = semester_sgpas(student.id)

    return render_template('student/dashboard.html', student=student, cga=cga, sgpa_data=sgpa_data)


@app.route('/profile')
def profile():
    if 'student_id' not in session:
        return redirect('/login')
    student = Student.query.get(session['student_id'])
    return render_template('student/profile.html', student=student)


@app.route('/student/notices')
def student_notices():
    if 'student_id' not in session:
        return redirect('/login')

    student = Student.query.get(session['student_id'])

    # Students see: college notices + their department notices + personal notices
    notices = (
        Notice.query
        .filter(
            (Notice.scope == "College") |
            ((Notice.scope == "Department") & (Notice.department_id == student.department_id)) |
            ((Notice.scope == "Student") & (Notice.student_id == student.id))
        )
        .order_by(Notice.id.desc())
        .all()
    )

    return render_template('public/notices.html', notices=notices)


@app.route('/student/events')
def student_events():
    if 'student_id' not in session:
        return redirect('/login')
    events = Event.query.all()
    return render_template('public/events.html', events=events)



@app.route("/student_materials")
def student_materials():

    if 'student_id' not in session:
        return redirect('/login')

    student = Student.query.get(session['student_id'])

    materials = Material.query.filter_by(
        department_id=student.department_id
    ).all()

    return render_template(
        "student/student_materials.html",
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

    return render_template('student/edit_profile.html', student=student)

@app.route("/student_results")
def student_results():

    if session.get("role") != "Student":
        return redirect("/login")

    student = Student.query.get(session["student_id"])

    results = Result.query.filter_by(
        student_id=student.id
    ).order_by(
        Result.semester,
        Result.subject_id
    ).all()

    return render_template(
        "student/my_results.html",
        student=student,
        results=results
    )

@app.route("/download_result")
def download_result():

    if "student_id" not in session:
        return redirect("/login")

    student = Student.query.get(session["student_id"])

    results = (
        Result.query
        .filter_by(student_id=student.id)
        .order_by(Result.semester, Result.subject_id)
        .all()
    )

    if not results:
        flash("No results available.", "warning")
        return redirect("/student_results")

    # ---------------- PDF ----------------

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=20,
        rightMargin=20,
        topMargin=20,
        bottomMargin=20
    )

    styles = getSampleStyleSheet()

    title_style = styles["Title"]
    title_style.alignment = TA_CENTER

    heading_style = styles["Heading2"]
    heading_style.alignment = TA_CENTER

    normal = styles["BodyText"]

    elements = []

    # Temp files to clean up after PDF build
    temp_files = []

    # Ensure placeholder assets exist (signatures, seal, photo)
    assets = ensure_static_assets()

    # ---------------- Logo ----------------

    logo_path = os.path.join("static", "image", "royal_logo.png")

    if os.path.exists(logo_path):
        logo = Image(logo_path)
        logo.drawWidth = 80
        logo.drawHeight = 80
        logo.hAlign = "CENTER"
        elements.append(logo)

    # ---------------- Heading ----------------

    elements.append(
        Paragraph(
            "<font size='22' color='#003366'><b>ROYAL COLLEGE</b></font>",
            title_style
        )
    )

    elements.append(
        Paragraph(
            "<font size='13' color='#003366'><b>Mira Road (East), Thane - 401107</b></font>",
            heading_style
        )
    )

    elements.append(
        Paragraph(
            "<font size='14'><b>Affiliated to University of Mumbai</b></font>",
            heading_style
        )
    )

    elements.append(
        Paragraph(
            "<font size='12' color='#0D47A1'><b>Accredited by NAAC 'A' Grade</b></font>",
            heading_style
        )
    )

    elements.append(
        Paragraph(
            "<font size='17' color='#1565C0'><b>OFFICIAL STUDENT MARKSHEET</b></font>",
            heading_style
        )
    )

    # University Seat / Roll Number
    seat_number = get_seat_number(student)

    elements.append(
        Paragraph(
            f"<font size='11' color='#003366'><b>University Seat No: {seat_number}</b></font>",
            heading_style
        )
    )

    elements.append(Spacer(1, 14))

    elements.append(
        HRFlowable(
            width="100%",
            thickness=2,
            color=colors.HexColor("#1565C0")
        )
    )

    elements.append(Spacer(1, 15))

    # ---------------- Student Information + Photograph ----------------

    display_id = get_display_student_id(student)

    student_info = [
        ["Student Name", student.name],
        ["University Seat No.", seat_number],
        ["Student ID", str(display_id)],
        ["Course", student.course],
        ["Semester", str(results[0].semester)],
        ["Academic Year", "2026-2027"],
        ["Date of Issue", datetime.now().strftime("%d-%m-%Y")]
    ]

    info_table = Table(
        student_info,
        colWidths=[150, 270]
    )

    info_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#1565C0")),
            ("TEXTCOLOR", (0, 0), (0, -1), colors.white),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 1, colors.grey),
            ("BACKGROUND", (1, 0), (1, -1), colors.whitesmoke),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
        ])
    )

    # Student photograph (auto-generated placeholder if missing)
    photo_path = generate_student_photo(student)
    photo_img = Image(photo_path)
    photo_img.drawWidth = 85
    photo_img.drawHeight = 95
    photo_img.hAlign = "CENTER"

    info_with_photo = Table(
        [[info_table, photo_img]],
        colWidths=[430, 95]
    )

    info_with_photo.setStyle(
        TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (1, 0), (1, 0), "CENTER"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ])
    )

    elements.append(info_with_photo)

    elements.append(Spacer(1, 25))

    # ---------------- Marks Table ----------------

    table_data = [[
        "Subject",
        "Credits",
        "Grade Point",
        "Internal",
        "Assignment",
        "External",
        "Practical",
        "Total",
        "Grade",
        "Status"
    ]]

    grand_total = 0

    for r in results:
        grand_total += r.total

        table_data.append([
            r.subject.subject_name,
            2,
            get_grade_point(r.grade),
            r.internal,
            r.assignment,
            r.external,
            r.practical,
            r.total,
            r.grade,
            r.status
        ])

    marks_table = Table(
        table_data,
        colWidths=[170, 55, 65, 55, 70, 55, 60, 50, 50, 55]
    )

    marks_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#003399")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 8),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ])
    )

    elements.append(marks_table)

    elements.append(Spacer(1, 20))

    # ---------------- Overall Summary ----------------

    percentage = grand_total / len(results)
    sgpa = calculate_sgpa(results)
    cgpa = calculate_cgpa(student.id)

    if percentage >= 90:
        grade = "A+"
    elif percentage >= 80:
        grade = "A"
    elif percentage >= 70:
        grade = "B+"
    elif percentage >= 60:
        grade = "B"
    elif percentage >= 50:
        grade = "C"
    elif percentage >= 40:
        grade = "D"
    else:
        grade = "F"

    status = "PASS" if percentage >= 40 else "FAIL"

    summary = [
        ["Overall Percentage", f"{percentage:.2f}%"],
        ["SGPA", f"{sgpa:.2f}"],
        ["CGPA", f"{cgpa:.2f}"],
        ["Overall Grade", grade],
        ["Result", status]
    ]

    summary_table = Table(
        summary,
        colWidths=[170, 120]
    )

    summary_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#0D47A1")),
            ("TEXTCOLOR", (0, 0), (0, -1), colors.white),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 1, colors.grey),
            ("BACKGROUND", (1, 0), (1, -1), colors.whitesmoke),
        ])
    )

    elements.append(summary_table)

    elements.append(Spacer(1, 20))

    # ---------------- Performance Summary Box ----------------

    total_subjects = len(results)
    total_credits = total_subjects * 2
    credits_earned = sum(
        2 for r in results if r.grade != "F"
    )

    performance_heading = Paragraph(
        "<font size='13' color='#003366'><b>PERFORMANCE SUMMARY</b></font>",
        heading_style
    )

    performance_data = [
        ["Total Subjects", str(total_subjects)],
        ["Total Credits", str(total_credits)],
        ["Credits Earned", str(credits_earned)],
        ["SGPA", f"{sgpa:.2f}"],
        ["CGPA", f"{cgpa:.2f}"],
        ["Overall Percentage", f"{percentage:.2f}%"],
        ["Result", status]
    ]

    performance_table = Table(
        performance_data,
        colWidths=[170, 120],
        hAlign="CENTER"
    )

    performance_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#0D47A1")),
            ("TEXTCOLOR", (0, 0), (0, -1), colors.white),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 1, colors.grey),
            ("BACKGROUND", (1, 0), (1, -1), colors.whitesmoke),
            ("ALIGN", (1, 0), (1, -1), "CENTER"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
        ])
    )

    elements.append(performance_heading)
    elements.append(Spacer(1, 10))
    elements.append(performance_table)

    elements.append(Spacer(1, 20))

    # ---------------- Semester-wise SGPA Table ----------------

    sgpa_data = semester_sgpas(student.id)

    if sgpa_data:

        sgpa_heading = Paragraph(
            "<font size='13' color='#003366'><b>SEMESTER-WISE SGPA</b></font>",
            heading_style
        )

        elements.append(sgpa_heading)

        elements.append(Spacer(1, 10))

        sgpa_table_data = [["Semester", "SGPA"]]

        for entry in sgpa_data:
            sgpa_table_data.append([
                f"Semester {entry['semester']}",
                f"{entry['sgpa']:.2f}"
            ])

        sgpa_table = Table(
            sgpa_table_data,
            colWidths=[150, 120]
        )

        sgpa_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1565C0")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
            ])
        )

        # Place SGPA table beside the SGPA bar chart
        graph_path = generate_sgpa_graph(sgpa_data, student)
        temp_files.append(graph_path)

        graph_img = Image(graph_path)
        graph_img.drawWidth = 250
        graph_img.drawHeight = 130
        graph_img.hAlign = "CENTER"

        sgpa_combined = Table(
            [[sgpa_table, graph_img]],
            colWidths=[270, 250]
        )

        sgpa_combined.setStyle(
            TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ])
        )

        elements.append(sgpa_combined)

        elements.append(Spacer(1, 20))

    elements.append(
        Paragraph(
            f"<b>Generated On:</b> {datetime.now().strftime('%d-%m-%Y %H:%M')}",
            normal
        )
    )

    elements.append(Spacer(1, 15))

    # ---------------- Result Declaration ----------------

    declaration = Table(
        [[Paragraph(
            "<i>This marksheet is computer generated and does not require a physical signature.</i>",
            normal
        )]],
        colWidths=[530]
    )

    declaration.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#E8F0FE")),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#1565C0")),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ])
    )

    elements.append(declaration)

    elements.append(Spacer(1, 15))

# ---------------- QR Code ----------------

    qr_data = f"""
ROYAL COLLEGE

Student Name : {student.name}
Student ID   : {display_id}
Course       : {student.course}
Semester     : {results[0].semester}

Percentage   : {percentage:.2f}%
Grade        : {grade}
Result       : {status}

Generated On : {datetime.now().strftime('%d-%m-%Y')}
"""

    qr = qrcode.make(qr_data)

    temp_qr = tempfile.NamedTemporaryFile(
        suffix=".png",
        delete=False
    )

    qr.save(temp_qr.name)

    qr_image = Image(temp_qr.name)
    qr_image.drawWidth = 75
    qr_image.drawHeight = 75

    # QR verification text
    qr_caption = Paragraph(
        "<font size='8' color='#555555'>Scan this QR Code<br/>to verify this marksheet.</font>",
        normal
    )

    # ---------------- Footer (Signatures + Seal + QR) ----------------

    coe_sign_path = os.path.join(
        "static", "image", "coe_signature.png"
    )
    principal_sign_path = os.path.join(
        "static", "image", "principal_signature.png"
    )
    seal_path = os.path.join(
        "static", "image", "college_seal.png"
    )

    coe_sign_img = Image(coe_sign_path)
    coe_sign_img.drawWidth = 90
    coe_sign_img.drawHeight = 40
    coe_sign_img.hAlign = "CENTER"

    principal_sign_img = Image(principal_sign_path)
    principal_sign_img.drawWidth = 90
    principal_sign_img.drawHeight = 40
    principal_sign_img.hAlign = "CENTER"

    seal_img = Image(seal_path)
    seal_img.drawWidth = 60
    seal_img.drawHeight = 60
    seal_img.hAlign = "CENTER"

    qr_table = Table(
        [[qr_image], [qr_caption]],
        colWidths=[120]
    )

    seal_line = HRFlowable(width=80, thickness=1, color=colors.black)
    sign_line = HRFlowable(width=110, thickness=1, color=colors.black)

    footer = Table(
        [
            [seal_img, principal_sign_img, coe_sign_img],
            [seal_line, sign_line, sign_line],
            [
                Paragraph("<b>College Seal</b>", normal),
                Paragraph("<b>Principal</b>", normal),
                Paragraph("<b>Controller of Examination</b>", normal)
            ],
            ["", qr_table, ""]
        ],
        colWidths=[180, 220, 220]
    )

    footer.setStyle(
        TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ])
    )

    elements.append(footer)

    # ---------------- Border + Watermark ----------------

    def draw_border(canvas, doc):
        canvas.saveState()

        # Outer border
        canvas.setStrokeColor(colors.HexColor("#1565C0"))
        canvas.setLineWidth(3)
        canvas.rect(
            20,
            20,
            doc.pagesize[0] - 40,
            doc.pagesize[1] - 40
        )

        # Draw diagonal "ROYAL COLLEGE" watermark behind content
        canvas.saveState()
        canvas.setFont("Helvetica-Bold", 70)
        canvas.setFillColor(colors.HexColor("#B0C4DE"))
        canvas.setFillAlpha(0.18)
        canvas.translate(doc.pagesize[0] / 2, doc.pagesize[1] / 2)
        canvas.rotate(45)
        canvas.drawCentredString(0, 0, "ROYAL COLLEGE")
        canvas.restoreState()

        canvas.restoreState()

    doc.build(
        elements,
        onFirstPage=draw_border,
        onLaterPages=draw_border
    )

    buffer.seek(0)

    # Clean up temp files (QR & graph)
    try:
        os.unlink(temp_qr.name)
    except Exception:
        pass

    for f in temp_files:
        try:
            os.unlink(f)
        except Exception:
            pass

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"{student.name}_Marksheet.pdf",
        mimetype="application/pdf"
    )

def get_grade_point(grade):
    grade_points = {
        "A+": 10,
        "A": 9,
        "B+": 8,
        "B": 7,
        "C": 6,
        "D": 5,
        "F": 0
    }

    return grade_points.get(grade, 0)


def calculate_sgpa(results):

    total_credit_points = 0
    total_credits = 0

    for result in results:

        credit = 2

        grade_point = get_grade_point(result.grade)

        total_credit_points += grade_point * credit

        total_credits += credit

    if total_credits == 0:
        return 0

    return round(total_credit_points / total_credits, 2)


def calculate_cgpa(student_id):

    semesters = (
        db.session.query(Result.semester)
        .filter_by(student_id=student_id)
        .distinct()
        .order_by(Result.semester)
        .all()
    )

    sgpa_list = []

    for semester in semesters:

        semester_results = Result.query.filter_by(
            student_id=student_id,
            semester=semester[0]
        ).all()

        sgpa_list.append(
            calculate_sgpa(semester_results)
        )

    if len(sgpa_list) == 0:
        return 0

    return round(sum(sgpa_list) / len(sgpa_list), 2)


def semester_sgpas(student_id):

    data = []

    semesters = (
        db.session.query(Result.semester)
        .filter_by(student_id=student_id)
        .distinct()
        .order_by(Result.semester)
        .all()
    )

    for semester in semesters:

        semester_results = Result.query.filter_by(
            student_id=student_id,
            semester=semester[0]
        ).all()

        data.append({
            "semester": semester[0],
            "sgpa": calculate_sgpa(semester_results)
        })

    return data


def get_seat_number(student):
    """Generate a university seat number based on the student ID."""
    course_code = "RC"
    if student.course:
        # Take first two letters of the first word in course name
        course_code = student.course.split()[0][:2].upper()

    return f"{course_code}{datetime.now().year}{student.id:04d}"


def get_display_student_id(student):
    """Return a clean sequential student ID (101, 102, ...) based on registration order."""
    try:
        all_students = Student.query.order_by(Student.id).all()
        for index, s in enumerate(all_students):
            if s.id == student.id:
                return index + 101
    except Exception:
        pass
    return student.id


def calculate_student_percentage(student_id):
    """Calculate average percentage for a student across all results."""
    results = Result.query.filter_by(student_id=student_id).all()
    if not results:
        return 0.0
    return round(sum(r.total for r in results) / len(results), 2)


def get_department_rankings():
    """Rank departments by average student percentage."""
    departments = Department.query.all()
    rankings = []

    for dept in departments:
        students = Student.query.filter_by(department_id=dept.id).all()
        total_pct = 0
        count = 0

        for s in students:
            pct = calculate_student_percentage(s.id)
            if pct > 0:
                total_pct += pct
                count += 1

        avg_pct = round(total_pct / count, 2) if count else 0.0

        rankings.append({
            "department": dept,
            "avg_percentage": avg_pct,
            "student_count": count
        })

    rankings.sort(key=lambda x: x["avg_percentage"], reverse=True)

    for i, r in enumerate(rankings):
        r["rank"] = i + 1

    return rankings


def get_class_toppers(limit=10):
    """Get top students across the whole college."""
    students = Student.query.all()
    toppers = []

    for s in students:
        pct = calculate_student_percentage(s.id)
        if pct > 0:
            toppers.append({
                "student": s,
                "percentage": pct,
                "cgpa": calculate_cgpa(s.id)
            })

    toppers.sort(key=lambda x: x["percentage"], reverse=True)

    return toppers[:limit]


def get_department_toppers():
    """Get class topper(s) for each department."""
    departments = Department.query.all()
    dept_toppers = []

    for dept in departments:
        students = Student.query.filter_by(department_id=dept.id).all()
        dept_students = []

        for s in students:
            pct = calculate_student_percentage(s.id)
            if pct > 0:
                dept_students.append({
                    "student": s,
                    "percentage": pct,
                    "cgpa": calculate_cgpa(s.id)
                })

        dept_students.sort(key=lambda x: x["percentage"], reverse=True)

        if dept_students:
            dept_toppers.append({
                "department": dept,
                "topper": dept_students[0],
                "top_3": dept_students[:3]
            })

    return dept_toppers


def ensure_static_assets():
    """Generate placeholder images (signatures, seal, photo) if they don't exist."""
    image_dir = os.path.join("static", "image")
    os.makedirs(image_dir, exist_ok=True)

    # Generate COE signature placeholder
    coe_path = os.path.join(image_dir, "coe_signature.png")
    if not os.path.exists(coe_path):
        img = PILImage.new("RGBA", (360, 120), (255, 255, 255, 0))
        draw = PILDraw.Draw(img)
        draw.line([(15, 80), (160, 55)], fill=(0, 51, 102, 255), width=3)
        draw.line([(160, 55), (300, 72)], fill=(0, 51, 102, 255), width=3)
        draw.arc((60, 5, 250, 115), 200, 340, fill=(0, 51, 102, 255), width=2)
        draw.text((15, 90), "Controller of Examination", fill=(0, 51, 102, 255))
        img.save(coe_path)

    # Generate Principal signature placeholder
    principal_path = os.path.join(image_dir, "principal_signature.png")
    if not os.path.exists(principal_path):
        img = PILImage.new("RGBA", (360, 120), (255, 255, 255, 0))
        draw = PILDraw.Draw(img)
        draw.line([(20, 55), (175, 70)], fill=(0, 51, 102, 255), width=3)
        draw.line([(175, 70), (330, 45)], fill=(0, 51, 102, 255), width=3)
        draw.arc((70, 0, 280, 120), 20, 160, fill=(0, 51, 102, 255), width=2)
        draw.text((15, 90), "Principal", fill=(0, 51, 102, 255))
        img.save(principal_path)

    # Generate college seal placeholder
    seal_path = os.path.join(image_dir, "college_seal.png")
    if not os.path.exists(seal_path):
        img = PILImage.new("RGB", (260, 260), (255, 255, 255))
        draw = PILDraw.Draw(img)
        draw.ellipse((10, 10, 250, 250), outline=(0, 51, 102, 255), width=6)
        draw.ellipse((30, 30, 230, 230), outline=(0, 51, 102, 255), width=2)
        draw.text((55, 115), "ROYAL COLLEGE", fill=(0, 51, 102, 255))
        draw.text((105, 135), "SEAL", fill=(0, 51, 102, 255))
        img.save(seal_path)

    return True


def generate_student_photo(student):
    """Generate a placeholder student photo if no real photo is available."""
    photo_dir = os.path.join("static", "image")
    os.makedirs(photo_dir, exist_ok=True)

    photo_path = os.path.join(photo_dir, f"student_{student.id}.png")

    if not os.path.exists(photo_path):
        img = PILImage.new("RGB", (220, 260), (245, 247, 250))
        draw = PILDraw.Draw(img)
        # Avatar head
        draw.ellipse((55, 20, 165, 130), fill=(176, 196, 222), outline=(100, 130, 160), width=2)
        # Body / shoulders
        draw.rounded_rectangle(
            (35, 140, 185, 250),
            radius=40,
            fill=(176, 196, 222),
            outline=(100, 130, 160),
            width=2
        )
        draw.text((60, 210), "PHOTO", fill=(70, 90, 120))
        img.save(photo_path)

    return photo_path


def generate_sgpa_graph(sgpa_data, student):
    """Generate a bar chart of semester-wise SGPA."""
    semesters = [f"S{e['semester']}" for e in sgpa_data]
    sgpas = [e["sgpa"] for e in sgpa_data]

    fig, ax = plt.subplots(figsize=(4.2, 2.2))
    bar_colors = [
        "#1565C0", "#42A5F5", "#64B5F6", "#1E88E5",
        "#0D47A1", "#82B1FF", "#1976D2", "#2196F3"
    ]

    ax.bar(
        semesters,
        sgpas,
        color=bar_colors[:len(semesters)],
        edgecolor="#0d47a1"
    )

    ax.set_ylim(0, 10)
    ax.set_ylabel("SGPA", fontsize=9)
    ax.set_xlabel("Semester", fontsize=9)
    ax.set_title("Semester-wise SGPA", fontsize=10, fontweight="bold")
    ax.tick_params(labelsize=8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Add value labels on top of each bar
    for i, v in enumerate(sgpas):
        ax.text(
            i, v + 0.15, f"{v:.2f}",
            ha="center", fontsize=8, fontweight="bold"
        )

    graph_path = os.path.join(
        "static", "image", f"sgpa_graph_{student.id}.png"
    )

    plt.tight_layout()
    fig.savefig(graph_path, dpi=120)
    plt.close(fig)

    return graph_path

# ==================== PRINCIPAL PERFORMANCE PAGES ====================

@app.route('/principal/department_rankings')
def principal_department_rankings():
    if session.get("role") != "Principal":
        return redirect("/login")
    department_rankings = get_department_rankings()
    return render_template('principal/department_rankings.html', department_rankings=department_rankings)


@app.route('/principal/college_toppers')
def principal_college_toppers():
    if session.get("role") != "Principal":
        return redirect("/login")
    class_toppers = get_class_toppers(limit=10)
    return render_template('principal/college_toppers.html', class_toppers=class_toppers)


@app.route('/principal/department_toppers')
def principal_department_toppers():
    if session.get("role") != "Principal":
        return redirect("/login")
    department_toppers = get_department_toppers()
    return render_template('principal/department_toppers.html', department_toppers=department_toppers)


# ==================== HOD PERFORMANCE PAGE ====================

@app.route('/hod/department_performance')
def hod_department_performance():
    if session.get("role") != "HOD":
        return redirect("/login")

    hod = User.query.get(session["user_id"])
    if hod is None:
        session.clear()
        flash("Session expired. Please login again.", "warning")
        return redirect("/login")

    performance_data = []
    department_avg = 0
    passed = 0
    failed = 0
    distinction = 0
    first_class = 0

    try:
        students = Student.query.filter_by(
            department_id=hod.department_id
        ).all()

        for s in students:
            pct = calculate_student_percentage(s.id)
            performance_data.append({
                "student": s,
                "percentage": pct,
                "cgpa": calculate_cgpa(s.id)
            })

        performance_data.sort(key=lambda x: x["percentage"], reverse=True)

        for i, d in enumerate(performance_data):
            d["rank"] = i + 1

        if performance_data:
            department_avg = round(
                sum(d["percentage"] for d in performance_data) / len(performance_data),
                2
            )

        passed = sum(1 for d in performance_data if d["percentage"] >= 40)
        failed = len(performance_data) - passed
        distinction = sum(1 for d in performance_data if d["percentage"] >= 75)
        first_class = sum(1 for d in performance_data if 60 <= d["percentage"] < 75)
    except Exception as perf_error:
        print("⚠️ Performance panel error (non-fatal):", perf_error)

    return render_template(
        'hod/department_performance.html',
        hod=hod,
        performance_data=performance_data,
        department_avg=department_avg,
        passed=passed,
        failed=failed,
        distinction=distinction,
        first_class=first_class
    )


# ==================== PRINCIPAL ROUTES ====================

@app.route( '/principal_dashboard')
def principal_dashboard():
    if session.get("role") != "Principal":
        return redirect("/login")

    # Department performance rankings
    department_rankings = get_department_rankings()

    # College-wide top students
    class_toppers = get_class_toppers(limit=10)

    # Topper from each department (top 3)
    department_toppers = get_department_toppers()

    return render_template(
        'principal/principal_dashboard.html',
        department_rankings=department_rankings,
        class_toppers=class_toppers,
        department_toppers=department_toppers
    )


@app.route('/students')
def students():
    if session.get("role") != "Principal":
        return redirect("/login")
    students_list = Student.query.all()
    return render_template('principal/students.html', students=students_list)


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
    "principal/edit_student.html",
    student=student,
    back_url=back_url
)


@app.route('/manage_notices', methods=['GET', 'POST'])
def manage_notices():
    print("Current session:", dict(session))
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
      "principal/manage_notices.html",
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
        "principal/edit_notice.html",
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
    return render_template('principal/manage_events.html', events=events)


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

    return render_template("principal/edit_event.html", event=event)


@app.route('/delete_event/<int:id>')
def delete_event(id):
    if session.get("role") != "Principal":
        return redirect("/login")

    event = Event.query.get_or_404(id)
    db.session.delete(event)
    db.session.commit()
    return redirect("/manage_events")

@app.route('/manage_hods')
def manage_hods():
    if session.get("role") != "Principal":
        return redirect('/login')

    hods = User.query.filter_by(role="HOD").all()
    return render_template('principal/manage_hods.html', hods=hods)


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
    return render_template("principal/add_hod.html", departments=departments)


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
    return render_template("principal/edit_hod.html", hod=hod, departments=departments)


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
    return render_template("principal/manage_teachers.html", teachers=teachers)


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
    return render_template("principal/add_teacher.html", departments=departments)


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
        "principal/edit_teacher.html",
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

    # Safety: if the current user is not found, redirect to login
    if hod is None:
        session.clear()
        flash("Session expired. Please login again.", "warning")
        return redirect("/login")

    department_id = hod.department_id or session.get("department_id")

    # Default summary values (safe if anything below fails)
    total_students = 0
    total_teachers = 0
    total_notices = 0
    total_materials = 0

    try:
        total_students = Student.query.filter_by(
            department_id=department_id
        ).count()

        total_teachers = User.query.filter_by(
            role="Teacher",
            department_id=department_id
        ).count()

        total_notices = Notice.query.filter_by(
            department_id=department_id
        ).count()

        total_materials = Material.query.filter_by(
            department_id=department_id
        ).count()
    except Exception as count_error:
        print("⚠️ HOD counts error (non-fatal):", count_error)

    # ---- Student Performance Panel ----
    performance_data = []
    department_avg = 0
    passed = 0
    failed = 0
    distinction = 0
    first_class = 0

    try:
        students = Student.query.filter_by(
            department_id=hod.department_id
        ).all()

        for s in students:
            pct = calculate_student_percentage(s.id)
            performance_data.append({
                "student": s,
                "percentage": pct,
                "cgpa": calculate_cgpa(s.id)
            })

        # Rank students by percentage (highest first)
        performance_data.sort(key=lambda x: x["percentage"], reverse=True)

        for i, d in enumerate(performance_data):
            d["rank"] = i + 1

        # Average department performance
        if performance_data:
            department_avg = round(
                sum(d["percentage"] for d in performance_data) / len(performance_data),
                2
            )

        # Pass / Fail summary
        passed = sum(1 for d in performance_data if d["percentage"] >= 40)
        failed = len(performance_data) - passed

        # Distinction / First class counts
        distinction = sum(1 for d in performance_data if d["percentage"] >= 75)
        first_class = sum(1 for d in performance_data if 60 <= d["percentage"] < 75)
    except Exception as perf_error:
        # Log but do NOT crash the dashboard if performance queries fail
        print("⚠️ Performance panel error (non-fatal):", perf_error)

    return render_template(
        "hod/hod_dashboard.html",
        hod=hod,
        total_students=total_students,
        total_teachers=total_teachers,
        total_notices=total_notices,
        total_materials=total_materials,
        performance_data=performance_data,
        department_avg=department_avg,
        passed=passed,
        failed=failed,
        distinction=distinction,
        first_class=first_class
    )

@app.route("/hod_students")
def hod_students():
    if session.get("role") != "HOD":
        return redirect("/login")

    students = Student.query.filter_by(
        department_id=session["department_id"]
    ).all()

    return render_template(
        "hod/hod_students.html",
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
        "hod/hod_teachers.html",
        teachers=teachers
    )

@app.route("/department_notices", methods=["GET", "POST"])
def department_notices():

    if session.get("role") != "HOD":
        return redirect("/login")

    hod = User.query.get(session["user_id"])

    if request.method == "POST":

        notice = Notice(
            title=request.form["title"],
            description=request.form["description"],
            scope="Department",
            department_id=hod.department_id,
            created_by=hod.id
        )

        db.session.add(notice)
        db.session.commit()

        flash("Department notice added successfully!", "success")

        return redirect("/department_notices")

    college_notices = Notice.query.filter_by(
        scope="College"
    ).all()

    department_notices = Notice.query.filter_by(
        scope="Department",
        department_id=hod.department_id
    ).all()

    return render_template(
        "hod/department_notices.html",
        college_notices=college_notices,
        department_notices=department_notices,
        role="HOD"
    )

@app.route("/department_events")
def department_events():

    if session.get("role") != "HOD":
        return redirect("/login")

    events = Event.query.all()

    return render_template(
        "public/events.html",
        events=events
    )

@app.route('/edit_department_notice/<int:id>', methods=['GET', 'POST'])
def edit_department_notice(id):
    print("SESSION:", dict(session))

    if session.get("role") not in ["Teacher", "HOD"]:
        return redirect("/login")

    user = User.query.get(session["user_id"])

    notice = Notice.query.get_or_404(id)

    # Security check
    if notice.scope != "Department" or notice.department_id != user.department_id:
        flash("You are not authorized to edit this notice.", "danger")

        if session["role"] == "Teacher":
            return redirect("/teacher_notices")
        else:
            return redirect("/department_notices")

    if request.method == "POST":

        notice.title = request.form["title"]
        notice.description = request.form["description"]

        db.session.commit()

        flash("Notice updated successfully!", "success")

        if session["role"] == "Teacher":
            return redirect("/teacher_notices")
        else:
            return redirect("/department_notices")

    return render_template(
        "hod/edit_notice.html",
        notice=notice
    )

@app.route('/delete_department_notice/<int:id>')
def delete_department_notice(id):

    if session.get("role") not in ["Teacher", "HOD"]:
        return redirect("/login")

    user = User.query.get(session["user_id"])

    notice = Notice.query.get_or_404(id)

    # Security check
    if notice.scope != "Department" or notice.department_id != user.department_id:
        flash("You are not authorized to delete this notice.", "danger")

        if session["role"] == "Teacher":
            return redirect("/teacher_notices")
        else:
            return redirect("/department_notices")

    db.session.delete(notice)
    db.session.commit()

    flash("Notice deleted successfully!", "success")

    if session["role"] == "Teacher":
        return redirect("/teacher_notices")
    else:
        return redirect("/department_notices")
    
@app.route("/study_materials")
def study_materials():

    if session.get("role") != "Teacher":
        return redirect("/login")

    teacher = User.query.get(session["user_id"])

    materials = Material.query.filter_by(
        department_id=teacher.department_id
    ).all()

    return render_template(
        "teacher/study_materials.html",
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
        "hod/department_attendance.html",
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
        created_by=session["user_id"],
        scope="Student",
        student_id=student.id
    )

    db.session.add(notice)
    db.session.commit()

    flash(f"Warning notice sent to {student.name} successfully!", "success")

    return redirect("/department_attendance")

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
        "teacher/teacher_dashboard.html",
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
        "hod/hod_students.html",
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

    return render_template("teacher/upload_material.html")

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
        "teacher/edit_material.html",
        material=material
    )

@app.route("/teacher_notices", methods=["GET", "POST"])
def teacher_notices():

    if session.get("role") != "Teacher":
        return redirect("/login")

    teacher = User.query.get(session["user_id"])

    if request.method == "POST":

        notice = Notice(
            title=request.form["title"],
            description=request.form["description"],
            scope="Department",
            department_id=teacher.department_id,
            created_by=teacher.id
        )

        db.session.add(notice)
        db.session.commit()

        flash("Notice added successfully!", "success")

        return redirect("/teacher_notices")

    college_notices = Notice.query.filter_by(
        scope="College"
    ).all()

    department_notices = Notice.query.filter_by(
        scope="Department",
        department_id=teacher.department_id
    ).all()

    return render_template(
    "hod/department_notices.html",
    college_notices=college_notices,
    department_notices=department_notices,
    role="Teacher"
)

@app.route("/teacher_events")
def teacher_events():

    if session.get("role") != "Teacher":
        return redirect("/login")

    events = Event.query.all()

    return render_template(
        "public/events.html",
        events=events
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

        # Check if today's attendance is already marked
        already_marked = Attendance.query.filter_by(
            department_id=teacher.department_id,
            date=today
        ).first()

        if already_marked:
            flash("Attendance for today has already been marked!", "warning")
            return redirect("/attendance")

        # Save attendance
        for student in students:

            status = request.form.get(f"status_{student.id}")

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
        "teacher/attendance.html",
        students=students,
        teacher=teacher,
        today=date.today()
    )

@app.route("/manage_results", methods=["GET", "POST"])
def manage_results():

    if session.get("role") != "Teacher":
        return redirect("/login")

    teacher = User.query.get(session["user_id"])

    students = Student.query.filter_by(
        department_id=teacher.department_id
    ).all()

    subjects = Subject.query.filter_by(
        department_id=teacher.department_id
    ).all()

    if request.method == "POST":

        student_id = request.form["student_id"]
        semester = int(request.form["semester"].replace("Semester ", ""))
        exam_type = request.form["exam_type"]

        subjects_list = request.form.getlist("subject[]")
        marks = request.form.getlist("marks[]")

        for subject_name, mark in zip(subjects_list, marks):

            subject = Subject.query.filter_by(
                subject_name=subject_name,
                semester=semester,
                department_id=teacher.department_id
            ).first()

            if not subject:
                continue

            result = Result.query.filter_by(
                student_id=student_id,
                subject_id=subject.id,
                semester=semester
            ).first()

            if not result:

                result = Result(
                    student_id=student_id,
                    teacher_id=teacher.id,
                    department_id=teacher.department_id,
                    subject_id=subject.id,
                    semester=semester,
                    internal=0,
                    assignment=0,
                    external=0,
                    practical=0
                )

                db.session.add(result)

            mark = int(mark)

            if exam_type == "Internal":
                result.internal = mark

            elif exam_type == "Assignment":
                result.assignment = mark

            elif exam_type == "External":
                result.external = mark

            elif exam_type == "Practical":
                result.practical = mark   # We'll improve this later

            result.total = (
                result.internal +
                result.assignment +
                result.external +
                result.practical
            )

            percentage = result.total

            if percentage >= 90:
                result.grade = "A+"
            elif percentage >= 80:
                result.grade = "A"
            elif percentage >= 70:
                result.grade = "B+"
            elif percentage >= 60:
                result.grade = "B"
            elif percentage >= 50:
                result.grade = "C"
            elif percentage >= 40:
                result.grade = "D"
            else:
                result.grade = "F"

            result.status = "PASS" if percentage >= 40 else "FAIL"

        db.session.commit()

        flash("Results Saved Successfully!", "success")

        return redirect("/manage_results")

    return render_template(
        "teacher/manage_results.html",
        students=students,
        subjects=subjects
    )

@app.route("/view_results")
def view_results():

    if session.get("role") != "Teacher":
        return redirect("/login")

    teacher = User.query.get(session["user_id"])

    results = (
        Result.query
        .filter_by(department_id=teacher.department_id)
        .order_by(Result.semester, Result.student_id, Result.subject_id)
        .all()
    )

    return render_template(
        "teacher/view_results.html",
        results=results
    )

@app.route("/get_subjects/<int:semester>")
def get_subjects(semester):

    if session.get("role") != "Teacher":
        return jsonify([])

    teacher = User.query.get(session["user_id"])

    subjects = Subject.query.filter_by(
        department_id=teacher.department_id,
        semester=semester
    ).all()

    return jsonify([
        {
            "id": s.id,
            "name": s.subject_name
        }
        for s in subjects
    ])

@app.route("/edit_result/<int:id>", methods=["GET", "POST"])
def edit_result(id):

    if session.get("role") != "Teacher":
        return redirect("/login")

    result = Result.query.get_or_404(id)

    if request.method == "POST":

        result.internal = int(request.form["internal"])
        result.assignment = int(request.form["assignment"])
        result.external = int(request.form["external"])
        result.practical = int(request.form["practical"])

        result.total = (
            result.internal +
            result.assignment +
            result.external +
            result.practical
        )

        if result.total >= 90:
            result.grade = "A+"
        elif result.total >= 80:
            result.grade = "A"
        elif result.total >= 70:
            result.grade = "B+"
        elif result.total >= 60:
            result.grade = "B"
        elif result.total >= 50:
            result.grade = "C"
        elif result.total >= 40:
            result.grade = "D"
        else:
            result.grade = "F"

        result.status = "PASS" if result.total >= 40 else "FAIL"

        db.session.commit()

        flash("Result Updated Successfully!", "success")

        return redirect("/view_results")

    return render_template(
        "teacher/edit_result.html",
        result=result
    )
@app.route("/delete_result/<int:id>")
def delete_result(id):

    if session.get("role") != "Teacher":
        return redirect("/login")

    result = Result.query.get_or_404(id)

    db.session.delete(result)
    db.session.commit()

    flash("Result Deleted Successfully!", "success")

    return redirect("/view_results")    

@app.route("/student_result/<int:student_id>", methods=["GET", "POST"])
def student_result(student_id):

    if session.get("role") != "Teacher":
        return redirect("/login")

    student = Student.query.get_or_404(student_id)

    if request.method == "POST":

        results = Result.query.filter_by(student_id=student_id).all()

        for result in results:

            result.internal = int(request.form[f"internal_{result.id}"])
            result.assignment = int(request.form[f"assignment_{result.id}"])
            result.external = int(request.form[f"external_{result.id}"])
            result.practical = int(request.form[f"practical_{result.id}"])

            result.total = (
                result.internal +
                result.assignment +
                result.external +
                result.practical
            )

            percentage = result.total

            if percentage >= 90:
                result.grade = "A+"
            elif percentage >= 80:
                result.grade = "A"
            elif percentage >= 70:
                result.grade = "B+"
            elif percentage >= 60:
                result.grade = "B"
            elif percentage >= 50:
                result.grade = "C"
            elif percentage >= 40:
                result.grade = "D"
            else:
                result.grade = "F"

            result.status = "PASS" if percentage >= 40 else "FAIL"

        db.session.commit()

        flash("Results Updated Successfully!", "success")

        return redirect(f"/student_result/{student_id}")

    results = Result.query.filter_by(student_id=student_id)\
        .order_by(Result.semester, Result.subject_id)\
        .all()

    return render_template(
        "teacher/student_result.html",
        student=student,
        results=results
    )
# ==================== DEPARTMENT PANEL OF HOME PAGE  ====================
@app.route("/department/<int:id>")
def department_details(id):

    department = Department.query.get_or_404(id)

    teachers = User.query.filter(
        User.department_id == id,
        User.role.in_(["Teacher", "HOD"])
    ).all()

    materials = Material.query.filter_by(
        department_id=id
    ).all()

    return render_template(
        "public/department_details.html",
        department=department,
        teachers=teachers,
        materials=materials,
    )
import re

@app.route("/download_material/<int:id>")
def download_material(id):

    material = Material.query.get_or_404(id)

    if "student_id" not in session:
        flash(
            "Please login as a registered student to download study materials.",
            "warning"
        )
        return redirect(url_for("login"))

    student = Student.query.get(session["student_id"])

    if not student:
        flash(
            "Your ID is not registered by the college administration. You cannot download study materials.",
            "danger"
        )
        return redirect(url_for("department_details", id=material.department_id))

    # Convert Google Drive preview link to direct download link
    match = re.search(r"/d/([^/]+)", material.link)

    if match:
        file_id = match.group(1)
        download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
        return redirect(download_url)

    return redirect(material.link)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)