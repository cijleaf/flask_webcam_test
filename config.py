import os
from os import path

basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    SECRET_KEY = '...'
    SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')
    # Set config values for Flask-Security.
    # We're using PBKDF2 with salt.
    SECURITY_PASSWORD_HASH = '...'
    SECURITY_PASSWORD_SALT = '...'
    SECURITY_POST_LOGIN_VIEW = '/admin'
    AWS_ACCESS_KEY_ID = '...'
    AWS_SECRET_ACCESS_KEY = '...'
    PROJECT_ROOT = path.dirname(__file__)


class DevelopmentConfig(Config):
    S3_BUCKET = "flask-webcam"
    DEVELOPMENT = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "postgresql://postgres:@localhost/flask-webcam"
    DATABASE_URL = SQLALCHEMY_DATABASE_URI