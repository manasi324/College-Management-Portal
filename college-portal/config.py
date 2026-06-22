class Config:
    SECRET_KEY = "collegeportal"

    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:1234@localhost/college_portal?charset=utf8"

    SQLALCHEMY_TRACK_MODIFICATIONS = False