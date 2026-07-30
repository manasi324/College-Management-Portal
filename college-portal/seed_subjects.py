from app import app
from models import db, Department, Subject


def add_subject(course, semester, department_name, subjects):

    department = Department.query.filter_by(
        name=department_name
    ).first()

    if not department:
        print(f"Department '{department_name}' not found!")
        return

    for subject in subjects:

        exists = Subject.query.filter_by(
            course=course,
            semester=semester,
            subject_name=subject
        ).first()

        if not exists:
            db.session.add(
                Subject(
                    course=course,
                    semester=semester,
                    subject_name=subject,
                    department_id=department.id
                )
            )


with app.app_context():

    print("Adding Subjects...")

    # ============================
    # BSC CS & IT
    # ============================

    add_subject(
        "BSC CS & IT",
        1,
        "BSC CS & IT",
        [
            "Digital Systems and Architecture",
            "Programming with Python-I",
            "Free and Open Source Software",
            "Database Systems",
            "Discrete Mathematics"
        ]
    )

    add_subject(
        "BSC CS & IT",
        2,
        "BSC CS & IT",
        [
            "Programming with C",
            "Programming with Python-II",
            "Data Structures",
            "Linux Operating System",
            "Calculus"
        ]
    )

    add_subject(
        "BSC CS & IT",
        3,
        "BSC CS & IT",
        [
            "Operating Systems",
            "Database Management Systems",
            "Design and Analysis of Algorithms",
            "Object Oriented Programming",
            "Computational Mathematics"
        ]
    )

    add_subject(
        "BSC CS & IT",
        4,
        "BSC CS & IT",
        [
            "Software Engineering",
            "Computer Networks",
            "Web Technologies",
            "Advanced Data Structures"
        ]
    )

    add_subject(
        "BSC CS & IT",
        5,
        "BSC CS & IT",
        [
            "Artificial Intelligence",
            "Enterprise Java",
            "Software Testing",
            "Information Security",
            "Internet of Things"
        ]
    )

    add_subject(
        "BSC CS & IT",
        6,
        "BSC CS & IT",
        [
            "Cloud Computing",
            "Data Mining",
            "DevOps",
            "Cyber Security",
            "Computer Vision"
        ]
    )

    db.session.commit()

    print("✅ BSC CS & IT subjects inserted successfully!")