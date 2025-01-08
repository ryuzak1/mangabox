from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Config:
    SESSION_TYPE = 'filesystem'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///manga.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
