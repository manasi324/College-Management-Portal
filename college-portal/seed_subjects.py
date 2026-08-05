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

    # ============================
    # BCOM
    # ============================

    add_subject(
        "BCOM",
        1,
        "BCOM",
        [
            "Financial Accounting",
            "Business Economics",
            "Business Communication",
            "Principles of Management",
            "Environmental Studies"
        ]
    )

    add_subject(
        "BCOM",
        2,
        "BCOM",
        [
            "Corporate Accounting",
            "Business Mathematics",
            "Macro Economics",
            "Company Law",
            "Marketing Management"
        ]
    )

    add_subject(
        "BCOM",
        3,
        "BCOM",
        [
            "Advanced Accounting",
            "Cost Accounting",
            "Income Tax",
            "Banking and Finance",
            "Auditing"
        ]
    )

    add_subject(
        "BCOM",
        4,
        "BCOM",
        [
            "Financial Management",
            "Management Accounting",
            "International Business",
            "Entrepreneurship",
            "Human Resource Management"
        ]
    )

    add_subject(
        "BCOM",
        5,
        "BCOM",
        [
            "Investment Management",
            "Corporate Finance",
            "Business Research Methods",
            "Financial Reporting",
            "Risk Management"
        ]
    )

    add_subject(
        "BCOM",
        6,
        "BCOM",
        [
            "Strategic Management",
            "Tax Planning",
            "Business Ethics",
            "Project Work",
            "Corporate Governance"
        ]
    )

    # ============================
    # BAF
    # ============================

    add_subject(
        "BAF",
        1,
        "BAF",
        [
            "Financial Accounting",
            "Business Economics",
            "Business Communication",
            "Foundation of Finance",
            "Introduction to Taxation"
        ]
    )

    add_subject(
        "BAF",
        2,
        "BAF",
        [
            "Corporate Accounting",
            "Business Mathematics",
            "Financial Management",
            "Company Law",
            "Auditing"
        ]
    )

    add_subject(
        "BAF",
        3,
        "BAF",
        [
            "Advanced Accounting",
            "Cost Accounting",
            "Income Tax",
            "Banking and Finance",
            "Financial Reporting"
        ]
    )

    add_subject(
        "BAF",
        4,
        "BAF",
        [
            "Management Accounting",
            "Investment Management",
            "International Finance",
            "Taxation-II",
            "Business Research"
        ]
    )

    add_subject(
        "BAF",
        5,
        "BAF",
        [
            "Financial Markets",
            "Strategic Finance",
            "Securities Analysis",
            "Derivatives",
            "Corporate Restructuring"
        ]
    )

    add_subject(
        "BAF",
        6,
        "BAF",
        [
            "Portfolio Management",
            "Financial Modeling",
            "Risk Analysis",
            "Project Finance",
            "Corporate Governance"
        ]
    )

    # ============================
    # BMS
    # ============================

    add_subject(
        "BMS",
        1,
        "BMS",
        [
            "Principles of Management",
            "Business Communication",
            "Business Accounting",
            "Business Environment",
            "Business Economics"
        ]
    )

    add_subject(
        "BMS",
        2,
        "BMS",
        [
            "Marketing Management",
            "Human Resource Management",
            "Financial Management",
            "Business Mathematics",
            "Organizational Behaviour"
        ]
    )

    add_subject(
        "BMS",
        3,
        "BMS",
        [
            "Managerial Economics",
            "Production Management",
            "Consumer Behaviour",
            "Business Law",
            "Research Methodology"
        ]
    )

    add_subject(
        "BMS",
        4,
        "BMS",
        [
            "Strategic Management",
            "Entrepreneurship",
            "Retail Management",
            "International Business",
            "Corporate Strategy"
        ]
    )

    add_subject(
        "BMS",
        5,
        "BMS",
        [
            "Operations Research",
            "Brand Management",
            "Supply Chain Management",
            "Business Analytics",
            "Leadership Skills"
        ]
    )

    add_subject(
        "BMS",
        6,
        "BMS",
        [
            "Strategic Marketing",
            "Change Management",
            "Business Ethics",
            "Project Management",
            "Global Business Strategy"
        ]
    )

    # ============================
    # BAMMC
    # ============================

    add_subject(
        "BAMMC",
        1,
        "BAMMC",
        [
            "Introduction to Media",
            "Fundamentals of Mass Communication",
            "Journalism Basics",
            "Media Writing",
            "Public Relations"
        ]
    )

    add_subject(
        "BAMMC",
        2,
        "BAMMC",
        [
            "Advertising",
            "Copywriting",
            "Media Studies",
            "Film Appreciation",
            "Radio and TV Production"
        ]
    )

    add_subject(
        "BAMMC",
        3,
        "BAMMC",
        [
            "Digital Media",
            "Creative Writing",
            "Media Ethics",
            "Event Management",
            "Social Media Marketing"
        ]
    )

    add_subject(
        "BAMMC",
        4,
        "BAMMC",
        [
            "Broadcast Journalism",
            "Print Production",
            "Media Research",
            "Corporate Communication",
            "Brand Management"
        ]
    )

    add_subject(
        "BAMMC",
        5,
        "BAMMC",
        [
            "News Writing",
            "Documentary Production",
            "Media Planning",
            "Content Writing",
            "Visual Communication"
        ]
    )

    add_subject(
        "BAMMC",
        6,
        "BAMMC",
        [
            "Media Law",
            "Communication Research",
            "New Media Technologies",
            "Portfolio Development",
            "Media Management"
        ]
    )

    db.session.commit()

    print("✅ All department subjects inserted successfully!")
