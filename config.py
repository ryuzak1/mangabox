from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Config:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///manga.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
