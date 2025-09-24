import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "abhishek"
    MYSQL_HOST = "localhost"
    MYSQL_USER = "root"
    MYSQL_PASSWORD = ""
    MYSQL_DB = "attan_manage"
