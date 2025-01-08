from flask import Blueprint, render_template, request, redirect, url_for,jsonify
from config import db
from app.models import Manga, Capitulo
from flask_paginate import Pagination, get_page_parameter
from datetime import datetime
import os
import requests
from bs4 import BeautifulSoup
from fpdf import FPDF
from PIL import Image
from io import BytesIO
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

routes = Blueprint('routes', __name__)

def baixar_imagens(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    content_div = soup.find('div', class_='content')
    p_tags = content_div.find_all('p')
    
    imagens = []
    for p in p_tags:
        img_tags = p.find_all('img')
        for img in img_tags:
            img_url = img['src']
            img_response = requests.get(img_url)
            img_data = Image.open(BytesIO(img_response.content)).convert('RGB')
            imagens.append(img_data)
    return imagens

def criar_pdf(imagens, nome_arquivo, qualidade=90, resolucao=(600, 760)):
    pdf = FPDF()
    temp_files = []
    for idx, imagem in enumerate(imagens):
        pdf.add_page()
        imagem_resized = imagem.resize(resolucao, Image.LANCZOS)
        img_temp = f"temp_img_{idx}.jpg"
        imagem_resized.save(img_temp, format='JPEG', quality=qualidade)
        pdf.image(img_temp, x=0, y=0, w=210, h=297)
        temp_files.append(img_temp)
    
    pdf.output(nome_arquivo)
    for temp_file in temp_files:
        os.remove(temp_file)

def processar_capitulos(url_base, capitulo_inicial, capitulo_final, manga_id, nome_manga, qualidade=90, resolucao=(600, 760)):
    capitulo_atual = float(capitulo_inicial)
    capitulo_final = float(capitulo_final)
    
    while capitulo_atual <= capitulo_final:
        try:
            if capitulo_atual.is_integer():
                capitulo_str = str(int(capitulo_atual))
            else:
                # Concatenar corretamente a parte inteira com a parte decimal
                parte_inteira = int(capitulo_atual)
                parte_decimal = int((capitulo_atual - parte_inteira) * 10)
                print(parte_decimal)
                print(parte_inteira)
                capitulo_str = parte_decimal
                print(capitulo_str)

            print(url_base)    
            url = f"{url_base}{capitulo_str}/"
            print(url)  
            logging.info(f'URL completa do capítulo: {url}')  # Adicionando log para verificar URL completa
            nome_capitulo = f"{nome_manga}-{capitulo_atual}"
            nome_arquivo_pdf = os.path.join('static', 'pdfs', f'{nome_capitulo}.pdf')
            if not os.path.exists('static/pdfs'):
                os.makedirs('static/pdfs')
            logging.info(f'Baixando imagens do capítulo {capitulo_atual} de {nome_manga}')
            imagens = baixar_imagens(url)
            logging.info(f'Criando PDF para o capítulo {capitulo_atual} de {nome_manga}')
            criar_pdf(imagens, nome_arquivo_pdf, qualidade, resolucao)
            novo_capitulo = Capitulo(numero=nome_capitulo, arquivo_pdf=f'pdfs/{nome_capitulo}.pdf', manga_id=manga_id)
            db.session.add(novo_capitulo)
            db.session.commit()
            logging.info(f'Capítulo {capitulo_atual} de {nome_manga} salvo com sucesso no banco de dados')
        except Exception as e:
            logging.error(f"Erro ao processar o capítulo {capitulo_atual} de {nome_manga}: {e}")

        capitulo_atual += 0.5


@routes.route('/')
def index():
    mangas = Manga.query.all()
    total_mangas = Manga.query.count()
    categorias = db.session.query(Manga.categoria, db.func.count(Manga.categoria)).group_by(Manga.categoria).all()
    return render_template('index.html', mangas=mangas, total_mangas=total_mangas, categorias=categorias)

@routes.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        nome = request.form['nome']
        descricao = request.form['descricao']
        categoria = request.form['categoria']
        url_base = request.form['url_base']
        capitulo_inicial = int(request.form['capitulo_inicial'])
        capitulo_final = int(request.form['capitulo_final'])
        
        novo_manga = Manga(nome=nome, descricao=descricao, categoria=categoria, url_base=url_base)
        db.session.add(novo_manga)
        db.session.commit()
        
        processar_capitulos(url_base, capitulo_inicial, capitulo_final, novo_manga.id, nome)
        
        return redirect(url_for('routes.index'))
    
    return render_template('add.html')


@routes.route('/add_full', methods=['GET', 'POST'], endpoint='add_full_manga')
def add_full_manga():
    if request.method == 'POST':
        url_base = request.form.get('url_base')
        capitulos_e_urls, manga_id, nome_manga = adicionar_manga_completo(url_base)
        total_chapters = len(capitulos_e_urls)

        response = {
            'total_chapters': total_chapters,
            'chapters': [{'number': capitulo, 'url': url, 'manga_id': manga_id, 'nome_manga': nome_manga} for capitulo, url in capitulos_e_urls if url]
        }
        return jsonify(response)
    
    return render_template('add_full.html')

def adicionar_manga_completo(url_base):
    import requests
    from bs4 import BeautifulSoup

    response = requests.get(url_base)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    sheader = soup.find('div', class_='sheader')
    if not sheader:
        logging.error("Div 'sheader' não encontrada.")
        return []

    data = sheader.find('div', class_='data')
    if not data:
        logging.error("Div 'data' não encontrada.")
        return []

    titulo = data.find('h1').get_text() if data.find('h1') else 'Título Não Encontrado'
    descricao = data.find('p').get_text() if data.find('p') else 'Descrição Não Encontrada'
    categoria = 'Indefinido'
    
    novo_manga = Manga(nome=titulo, descricao=descricao, categoria=categoria, url_base=url_base)
    db.session.add(novo_manga)
    db.session.commit()
    
    episodios = soup.find('ul', class_='episodios')
    if not episodios:
        logging.error("UL 'episodios' não encontrada.")
        return []

    capitulos_e_urls = []

    for episodio in episodios.find_all('li'):
        capitulo_url = episodio.find('a')['href'] if episodio.find('a') else None
        episodiotitle = episodio.find('div', class_='episodiotitle')
        
        if episodiotitle:
            numero_capitulo_text = episodiotitle.find('a').contents[0].strip()
            numero_capitulo = numero_capitulo_text.split("Capítulo")[-1].strip()
            logging.info(f"Número do capítulo encontrado: {numero_capitulo}")
            capitulos_e_urls.append((numero_capitulo, capitulo_url))
        else:
            logging.error(f"Div com a classe 'episodiotitle' não encontrada para o URL: {capitulo_url}")
            capitulos_e_urls.append((None, capitulo_url))

    return capitulos_e_urls, novo_manga.id, titulo


@routes.route('/process_chapter', methods=['POST'])
def processar_capitulo_route():
    chapter_url = request.form.get('chapter_url')
    chapter_number = request.form.get('chapter_number')
    manga_id = request.form.get('manga_id')
    nome_manga = request.form.get('nome_manga')
    url_tratada = chapter_url.rsplit('-', 1)[0] + '-'
    processar_capitulos(url_tratada, float(chapter_number), float(chapter_number), manga_id, nome_manga)
    return jsonify(success=True)












@routes.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    manga = Manga.query.get_or_404(id)
    if request.method == 'POST':
        manga.nome = request.form['nome']
        manga.descricao = request.form['descricao']
        manga.categoria = request.form['categoria']
        
        db.session.commit()
        return redirect(url_for('routes.index'))
    
    return render_template('edit.html', manga=manga)

@routes.route('/listar_mangas')
def listar_mangas():
    query = request.args.get('query')
    page = request.args.get(get_page_parameter(), type=int, default=1)
    if query:
        mangas_query = Manga.query.filter(Manga.nome.like(f'%{query}%'))
    else:
        mangas_query = Manga.query

    total = mangas_query.count()
    mangas = mangas_query.paginate(page=page, per_page=10).items
    pagination = Pagination(page=page, total=total, search=query, record_name='mangas', per_page=10, css_framework='bootstrap4')
    
    return render_template('listar_mangas.html', mangas=mangas, query=query, pagination=pagination)

@routes.route('/delete_manga/<int:id>', methods=['POST'])
def delete_manga(id):
    manga = Manga.query.get_or_404(id)
    if manga:
        # Excluir todos os capítulos relacionados
        capitulos = Capitulo.query.filter_by(manga_id=manga.id).all()
        for capitulo in capitulos:
            caminho_arquivo = os.path.join('static', capitulo.arquivo_pdf)
            if os.path.exists(caminho_arquivo):
                os.remove(caminho_arquivo)
            db.session.delete(capitulo)
        
        db.session.delete(manga)
        db.session.commit()
    return redirect(url_for('routes.listar_mangas'))


@routes.route('/capitulos')
def capitulos():
    query = request.args.get('query')
    page = request.args.get(get_page_parameter(), type=int, default=1)
    if query:
        capitulos_query = Capitulo.query.filter(Capitulo.numero.like(f'%{query}%')).order_by(Capitulo.data_cadastro.desc())
    else:
        capitulos_query = Capitulo.query.order_by(Capitulo.data_cadastro.desc())

    total = capitulos_query.count()
    capitulos = capitulos_query.paginate(page=page, per_page=10).items
    pagination = Pagination(page=page, total=total, search=query, record_name='capitulos', per_page=10, css_framework='bootstrap4')
    
    return render_template('capitulos.html', capitulos=capitulos, query=query, pagination=pagination)

@routes.route('/add_chapter/<int:id>', methods=['GET', 'POST'])
def add_chapter(id):
    manga = Manga.query.get_or_404(id)
    if request.method == 'POST':
        numero_capitulo = request.form['numero_capitulo']
        url_base = manga.url_base
        processar_capitulos(url_base, int(numero_capitulo), int(numero_capitulo), manga.id, manga.nome)
        return redirect(url_for('routes.listar_mangas'))
    
    return render_template('add_chapter.html', manga=manga)



@routes.route('/edit_capitulo/<int:id>', methods=['GET', 'POST'])
def edit_capitulo(id):
    capitulo = Capitulo.query.get_or_404(id)
    if request.method == 'POST':
        novo_nome = request.form['nome']
        antigo_arquivo_pdf = os.path.join('static', capitulo.arquivo_pdf)

        # Novo nome do arquivo PDF
        novo_arquivo_pdf = os.path.join('static', 'pdfs', f'{novo_nome}.pdf')

        # Renomear o arquivo PDF se ele existir
        if os.path.exists(antigo_arquivo_pdf):
            os.rename(antigo_arquivo_pdf, novo_arquivo_pdf)
        else:
            novo_arquivo_pdf = capitulo.arquivo_pdf

        # Atualizar o nome do capítulo e o nome do arquivo PDF no banco de dados
        capitulo.numero = novo_nome
        capitulo.arquivo_pdf = f'pdfs/{novo_nome}.pdf'
        db.session.commit()

        return redirect(url_for('routes.capitulos'))

    return render_template('edit_capitulo.html', capitulo=capitulo)


@routes.route('/delete_capitulo/<int:id>', methods=['POST'])
def delete_capitulo(id):
    capitulo = Capitulo.query.get_or_404(id)
    if capitulo:
        # Verifica se o arquivo existe antes de tentar deletá-lo
        caminho_arquivo = os.path.join('static', capitulo.arquivo_pdf)
        if os.path.exists(caminho_arquivo):
            os.remove(caminho_arquivo)
        
        db.session.delete(capitulo)
        db.session.commit()
    return redirect(url_for('routes.capitulos'))







