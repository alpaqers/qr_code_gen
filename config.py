import os

class DevelopmentConfig():
    SECRET_KEY = 'qwerty'
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:qwerty@localhost:5432/twojqr_local'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class ProductionConfig():
    SECRET_KEY = 'qwerty'
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
