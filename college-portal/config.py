class Config:
    SECRET_KEY = "collegeportal"

    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://3wKtk5Hdna3qnnA.root:jxkymUKYGgPE8DEL@gateway01.ap-northeast-1.prod.aws.tidbcloud.com:4000/college_portal"

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SQLALCHEMY_ENGINE_OPTIONS = {
        "connect_args": {
            "ssl": {
                "ca": r"C:\Users\Admin\Downloads\isrgrootx1.pem"

            }
        }
    }