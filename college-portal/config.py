class Config:
    SECRET_KEY = "collegeportal"

    SQLALCHEMY_DATABASE_URI = \
    "mysql+pymysql://root:password@localhost/college_portal"

    SQLALCHEMY_TRACK_MODIFICATIONS = False
