from flask import Flask
from config import Config, db
from app.routes import routes

def create_app():
    app = Flask(__name__, static_folder='../static', template_folder='../templates')
    app.config.from_object(Config)
    db.init_app(app)
    app.register_blueprint(routes)
    return app
