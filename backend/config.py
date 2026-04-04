import os 
from dotenv import load_dotenv 

load_dotenv()

class Config():
    DEBUG = False
    SQL_ALCHEMY_TRACK_MODIFICATIONS = False 

class LocalDevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI')
    SECURITY_PASSWORD_HASH = os.getenv('SECURITY_PASSWORD_HASH')
    SECURITY_PASSWORD_SALT = os.getenv('SECURITY_PASSWORD_SALT')
    SECRET_KEY = os.getenv('SECRET_KEY')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')

    WTF_CSRF_ENABLED = False