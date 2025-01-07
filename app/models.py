from datetime import datetime
from config import db

class Manga(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.String(200), nullable=False)
    categoria = db.Column(db.String(50), nullable=False)
    url_base = db.Column(db.String(200), nullable=False)
    capitulos = db.relationship('Capitulo', backref='manga', lazy=True)

class Capitulo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(200), nullable=False)
    arquivo_pdf = db.Column(db.String(200), nullable=False)
    data_cadastro = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    manga_id = db.Column(db.Integer, db.ForeignKey('manga.id'), nullable=False)
