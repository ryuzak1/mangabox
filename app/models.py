from datetime import datetime
from config import db

class Manga(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.String(200), nullable=False)
    categoria = db.Column(db.String(50), nullable=False)
    url_base = db.Column(db.String(200), nullable=False)
    capa = db.Column(db.String(200), nullable=True)  # Novo campo para a imagem da capa
    ano_lancamento = db.Column(db.String(4), nullable=True)  # Novo campo para o ano de lançamento
    nota = db.Column(db.String(10), nullable=True)  # Novo campo para a nota
    data_adicao = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)  # Campo para data de adição
    capitulos = db.relationship('Capitulo', backref='manga', lazy=True)

class Capitulo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(200), nullable=False)
    arquivo_pdf = db.Column(db.String(200), nullable=False)
    data_cadastro = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    manga_id = db.Column(db.Integer, db.ForeignKey('manga.id'), nullable=False)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    data_cadastro = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f'<User {self.username}>'
