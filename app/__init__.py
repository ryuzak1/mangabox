from flask import Flask
from config import Config, db
from flask_migrate import Migrate
from flask_session import Session

def create_app():
    app = Flask(__name__, static_folder='../static', template_folder='../templates')
    app.config.from_object(Config)
    app.secret_key = 'sua_chave_secreta'  # Adicione uma chave secreta para sessões
    
    db.init_app(app)
    Migrate(app, db)  # Configurar Flask-Migrate
    Session(app)  # Inicializar a sessão

    with app.app_context():
        from app.routes import routes  # Importar rotas dentro do contexto do aplicativo
        app.register_blueprint(routes)
    
    return app
