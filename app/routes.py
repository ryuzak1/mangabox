from flask import Blueprint, render_template, request, redirect, url_for,jsonify,session,flash
from config import db
from app.models import Manga, Capitulo, User
from flask_paginate import Pagination, get_page_parameter
from datetime import datetime
import os
import requests
from bs4 import BeautifulSoup
from fpdf import FPDF
from PIL import Image
from io import BytesIO
import logging
from functools import wraps
import re
from werkzeug.security import generate_password_hash, check_password_hash

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

def baixar_imagens_fonte_2(url):


    logging.info(f"Buscando URL: {url}+?style=list")
    url=url+"?style=list"
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException as e:
        logging.error(f"Erro ao fazer a requisição para a URL {url}: {e}")
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    reading_content = soup.find('div', class_='reading-content')
    
    if not reading_content:
        logging.warning("Div 'reading-content' não encontrada")
        return []

    logging.info("Div 'reading-content' encontrada")

    page_breaks = reading_content.find_all('div', class_='page-break')
    if not page_breaks:
        logging.warning("Divs 'page-break' não encontradas dentro de 'reading-content'")
        return []

    imagens = []
    for i, page_break in enumerate(page_breaks):
        img_tag = page_break.find('img')
        if img_tag:
            img_url = img_tag.get('data-src') or img_tag.get('src')
            logging.info(f"URL da Imagem: {img_url}")

            try:
                img_response = requests.get(img_url)
                img_response.raise_for_status()
                img_data = Image.open(BytesIO(img_response.content)).convert('RGB')
                imagens.append(img_data)
            except requests.RequestException as e:
                logging.error(f"Erro ao baixar a imagem da URL {img_url}: {e}")
            except Exception as e:
                logging.error(f"Erro ao processar a imagem da URL {img_url}: {e}")
        else:
            logging.warning(f"Tag 'img' não encontrada dentro de 'page-break' {i+1}")

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

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from PIL import Image
import io
import os


def dividir_e_ajustar_imagem(imagem, largura_pagina, altura_pagina, limite_altura=2000):
    largura, altura = imagem.size

    if altura > limite_altura:
        # Ajustar a largura da imagem para caber na página
        proporcao = largura_pagina / largura
        nova_altura = int(altura * proporcao)
        imagem_redimensionada = imagem.resize((largura_pagina, nova_altura), Image.LANCZOS)
        
        # Dividir a imagem redimensionada em partes que cabem na página
        partes = []
        topo = 0
        while topo < nova_altura:
            parte_inferior = min(topo + altura_pagina, nova_altura)
            parte = imagem_redimensionada.crop((0, topo, largura_pagina, parte_inferior))
            partes.append(parte)
            topo += altura_pagina
        return partes
    else:
        # Redimensionar a imagem sem cortar
        imagem_resized = imagem.resize((largura_pagina, altura_pagina), Image.LANCZOS)
        return [imagem_resized]



from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import io
import os

def criar_pdf_fonte_2(imagens, nome_arquivo, qualidade=90):
    largura_pagina, altura_pagina = int(A4[0]), int(A4[1])
    c = canvas.Canvas(nome_arquivo, pagesize=A4)
    temp_files = []

    for idx, imagem in enumerate(imagens):
        partes = dividir_e_ajustar_imagem(imagem, largura_pagina, altura_pagina)
        for parte_idx, parte in enumerate(partes):
            buffer = io.BytesIO()
            parte.save(buffer, format="JPEG", quality=qualidade)
            buffer.seek(0)
            temp_file = f"temp_img_{idx}_{parte_idx}.jpg"
            with open(temp_file, 'wb') as f:
                f.write(buffer.getbuffer())
            temp_files.append(temp_file)

            if os.path.exists(temp_file):
                c.drawImage(temp_file, 0, 0, largura_pagina, altura_pagina, preserveAspectRatio=True)
                c.showPage()
            else:
                logging.error(f"Erro: o arquivo temporário {temp_file} não foi encontrado.")

    c.save()

    # Remover arquivos temporários
    for temp_file in temp_files:
        if os.path.exists(temp_file):
            os.remove(temp_file)
        else:
            logging.error(f"Erro: o arquivo temporário {temp_file} não foi encontrado para remoção.")


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
            logging.info(f'URL completa do capítulo Fonte 1: {url}')  # Adicionando log para verificar URL completa
            nome_capitulo = f"{nome_manga}-{capitulo_atual}"
            nome_arquivo_pdf = os.path.join('static', 'pdfs', f'{nome_capitulo}.pdf')
            if not os.path.exists('static/pdfs'):
                os.makedirs('static/pdfs')
            logging.info(f'Baixando imagens do capítulo {capitulo_atual} de {nome_manga}')
            imagens = baixar_imagens(url)
            logging.info(f'Criando PDF para o capítulo {capitulo_atual} de {nome_manga}')
            criar_pdf(imagens, nome_arquivo_pdf, qualidade, resolucao)
            novo_capitulo = Capitulo(numero=capitulo_atual, arquivo_pdf=f'pdfs/{nome_capitulo}.pdf', manga_id=manga_id)
            db.session.add(novo_capitulo)
            db.session.commit()
            logging.info(f'Capítulo {capitulo_atual} de {nome_manga} salvo com sucesso no banco de dados')
        except Exception as e:
            logging.error(f"Erro ao processar o capítulo {capitulo_atual} de {nome_manga}: {e}")

        capitulo_atual += 0.5

def processar_capitulos_fonte_2(url_base, capitulo_inicial, capitulo_final, manga_id, nome_manga, qualidade=90, resolucao=(600, 760)):
    capitulo_atual = float(capitulo_inicial)
    capitulo_final = float(capitulo_final)
    
    nome_manga_limpo = re.sub(r'\s+', ' ', nome_manga).strip()  # Remover novas linhas e espaços extras

    while capitulo_atual <= capitulo_final:
        try:
            if capitulo_atual.is_integer():
                capitulo_str = str(int(capitulo_atual)).zfill(2)  # Formatar com dois dígitos
                logging.info(f'CAPITULO INTEIRO PARA SER SALVO:{capitulo_str}')
            else:
                parte_inteira = int(capitulo_atual)
                parte_decimal = int((capitulo_atual - parte_inteira) * 10)
                capitulo_str = f"{parte_inteira:02d}-{parte_decimal}"  # Formatar a parte inteira com dois dígitos
                logging.info(f"CAPITULO DECIMAL PARA SER SALVO:{capitulo_str}")

            url = f"{url_base}{capitulo_str}/"
            logging.info(f'URL completa do capítulo: {url}')
            nome_capitulo = f"{nome_manga_limpo}-{capitulo_str}"
            nome_arquivo_pdf = os.path.join('static', 'pdfs', f'{nome_capitulo}.pdf')
            if not os.path.exists('static/pdfs'):
                os.makedirs('static/pdfs')
            logging.info(f'Baixando imagens do capítulo {capitulo_str} de {nome_manga}')
            
            imagens = baixar_imagens_fonte_2(url)
            logging.info(f'Criando PDF para o capítulo {capitulo_str} de {nome_manga}')
            criar_pdf_fonte_2(imagens, nome_arquivo_pdf, qualidade)

            logging.info(f"CAPITULO PARA SER SALVO:{capitulo_atual}")
            numeroCapitulo = str(capitulo_atual)

            novo_capitulo = Capitulo(numero=numeroCapitulo, arquivo_pdf=f'pdfs/{nome_capitulo}.pdf', manga_id=manga_id)
            db.session.add(novo_capitulo)
            db.session.commit()
            logging.info(f'Capítulo {capitulo_str} de {nome_manga} salvo com sucesso no banco de dados')

        except Exception as e:
            logging.error(f"Erro ao processar o capítulo {capitulo_str} de {nome_manga}: {e}")

        capitulo_atual += 0.5



def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('routes.login'))
        return f(*args, **kwargs)
    return decorated_function


@routes.route('/')
def home():
    return redirect(url_for('routes.inicial'))

@routes.route('/_admin')
@login_required
def home_admin():
    total_mangas = Manga.query.count()
    total_capitulos = Capitulo.query.count()
    mangas = Manga.query.order_by(Manga.id.desc()).limit(5).all()
    return render_template('index.html', total_mangas=total_mangas, total_capitulos=total_capitulos, mangas=mangas)


@routes.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Buscar usuário no banco de dados
        user = User.query.filter_by(username=username).first()

        # Verificar se o usuário existe e a senha está correta
        if user and check_password_hash(user.password, password):
            # Verificar se o usuário é administrador
            if user.is_admin:
                session['user'] = username
                print('logado')
                return redirect(url_for('routes.home'))
            else:
                print('Acesso negado: você não é um administrador.')
                flash('Acesso negado: você não é um administrador.')
        else:
            print('ERRO AO LOGAR USUARIO OU SENHA INCORRETOS')
            flash('Usuário ou senha incorretos!')
    
    return render_template('login.html')




@routes.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        nome = request.form['nome']
        descricao = request.form['descricao']
        categoria = request.form['categoria']
        url_base = request.form['url_base']
        capa = request.files['capa']
        
        # Salvar a imagem da capa
        if capa and capa.filename != '':
            capa_filename = f"{nome.replace(' ', '_')}_cover.jpg"
            capa_path = os.path.join('static', 'covers', capa_filename)
            os.makedirs(os.path.dirname(capa_path), exist_ok=True)
            capa.save(capa_path)
        else:
            capa_filename = None

        novo_manga = Manga(nome=nome, descricao=descricao, categoria=categoria, url_base=url_base, capa=capa_filename)
        db.session.add(novo_manga)
        db.session.commit()
        
        return redirect(url_for('routes.listar_mangas'))
    
    return render_template('add.html')





@routes.route('/add_full', methods=['GET', 'POST'], endpoint='add_full_manga')
@login_required
def add_full_manga():
    if request.method == 'POST':
        url_base = request.form.get('url_base')
        fonte = request.form.get('fonte')

        if fonte == '1':
            capitulos_e_urls, manga_id, nome_manga, categorias = adicionar_manga_completo(url_base)
        elif fonte == '2':
            capitulos_e_urls, manga_id, nome_manga, categorias = adicionar_manga_completo_fonte_2(url_base)
        else:
            return jsonify({'error': 'Fonte inválida'}), 400

        total_chapters = len(capitulos_e_urls)

        response = {
            'total_chapters': total_chapters,
            'chapters': [{'number': capitulo, 'url': url, 'manga_id': manga_id, 'nome_manga': nome_manga, 'categorias': categorias} for capitulo, url in capitulos_e_urls if url]
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
    
    # Obter ambas as tags <p> que contêm a descrição
    descricao_tags = data.find_all('p')
    descricao = ' '.join([p.get_text() for p in descricao_tags if p])  # Concatenar texto de todas as tags <p>

    # Obter categorias
    generos_div = soup.find('div', class_='sgeneros')
    categorias = []
    if generos_div:
        categorias = [a.get_text().strip() for a in generos_div.find_all('a')]

    # Obter URL da imagem da capa
    poster_div = sheader.find('div', class_='poster')
    poster_url = poster_div.find('img')['src'] if poster_div and poster_div.find('img') else None

    # Obter ano de lançamento
    extra_div = soup.find('div', class_='extra')
    ano_lancamento = extra_div.find('span', class_='date').get_text() if extra_div and extra_div.find('span', class_='date') else 'Ano Não Encontrado'

    # Obter nota
    nota_span = soup.find('span', class_='dt_rating_vgs')
    nota = nota_span.get_text().strip() if nota_span else 'Nota Não Encontrada'

    # Log do link da imagem de capa para verificar
    logging.info(f"URL da imagem de capa: {poster_url}")

    # Baixar a imagem da capa se a URL estiver disponível
    if poster_url:
        try:
            logging.info("Iniciando download da imagem de capa.")
            img_data = requests.get(poster_url).content
            img_name = f"{titulo.replace(' ', '_')}_cover.jpg"
            img_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'static', 'covers', img_name)  # Usar o diretório existente

            # Criar o diretório se não existir
            os.makedirs(os.path.dirname(img_path), exist_ok=True)

            # Salvar a imagem da capa localmente
            with open(img_path, 'wb') as handler:
                handler.write(img_data)
            logging.info(f"Imagem de capa salva com sucesso em {img_path}.")

            # Verificar se o arquivo foi salvo e obter seu tamanho
            if os.path.exists(img_path):
                file_size = os.path.getsize(img_path)
                logging.info(f"Arquivo salvo: {img_path} ({file_size} bytes)")
            else:
                logging.error("Erro: o arquivo da imagem de capa não foi encontrado no diretório.")

        except Exception as e:
            logging.error(f"Erro ao baixar ou salvar a imagem de capa: {e}")
            img_name = None
    else:
        logging.warning("URL da imagem de capa não encontrada.")
        img_name = None

    categoria = ', '.join(categorias)  # Converter lista de categorias em string

    novo_manga = Manga(nome=titulo, descricao=descricao, categoria=categoria, ano_lancamento=ano_lancamento, nota=nota, url_base=url_base, capa=img_name)
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
            logging.info(f"Capítulo: {numero_capitulo}, URL: {capitulo_url}")
            capitulos_e_urls.append((None, capitulo_url))

    return capitulos_e_urls, novo_manga.id, titulo, categorias

def adicionar_manga_completo_fonte_2(url_base):
    import requests
    from bs4 import BeautifulSoup
    import logging
    from PIL import Image
    from io import BytesIO
    import os
    import re

    logging.info(f"Buscando URL base: {url_base}")
    
    response = requests.get(url_base)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Título do Mangá
    post_title = soup.find('div', class_='post-title')
    titulo = post_title.find('h1').get_text() if post_title and post_title.find('h1') else 'Título Não Encontrado'
    logging.info(f"Título do Mangá: {titulo}")
    
    # Descrição
    summary_content = soup.find('div', class_='summary__content')
    descricao = summary_content.get_text().strip() if summary_content else 'Descrição Não Encontrada'
    logging.info(f"Descrição: {descricao}")
    
    # Categorias
    genres_content = soup.find('div', class_='genres-content')
    categorias = list(set([a.get_text().strip() for a in genres_content.find_all('a')])) if genres_content else []
    logging.info(f"Categorias: {categorias}")
    
    # URL da Imagem da Capa
    summary_image = soup.find('div', class_='summary_image')
    if summary_image:
        logging.info("Encontrado 'summary_image'")
        anchor_tag = summary_image.find('a')
        if anchor_tag:
            logging.info("Encontrado 'a' dentro de 'summary_image'")
            img_tag = anchor_tag.find('img')
            if img_tag:
                poster_url = img_tag['data-src']
                logging.info(f"URL da Imagem da Capa: {poster_url}")
            else:
                poster_url = None
                logging.warning("'img' não encontrada dentro de 'a'")
        else:
            poster_url = None
            logging.warning("'a' não encontrada dentro de 'summary_image'")
    else:
        poster_url = None
        logging.warning("'summary_image' não encontrada")

    # Ano de Lançamento
    summary_content_wrap = soup.find('div', class_='summary_content_wrap')
    if summary_content_wrap:
        logging.info("Encontrado 'summary_content_wrap'")
        summary_content = summary_content_wrap.find('div', class_='summary_content')
        if summary_content:
            logging.info("Encontrado 'summary_content'")
            post_status = summary_content.find('div', class_='post-status')
            if post_status:
                logging.info("Encontrado 'post-status'")
                summary_content_inner = post_status.find('div', class_='summary-content')
                if summary_content_inner:
                    logging.info("Encontrado 'summary-content' dentro de 'post-status'")
                    a_tag = summary_content_inner.find('a')
                    if a_tag:
                        ano_lancamento = a_tag.get_text().strip()
                        logging.info(f"Conteúdo da tag <a>: {ano_lancamento}")
                    else:
                        ano_lancamento = 'Ano Não Encontrado'
                        logging.warning("'a' não encontrada dentro de 'summary-content'")
                else:
                    ano_lancamento = 'Ano Não Encontrado'
                    logging.warning("'summary-content' não encontrada dentro de 'post-status'")
            else:
                ano_lancamento = 'Ano Não Encontrado'
                logging.warning("'post-status' não encontrada dentro de 'summary_content'")
        else:
            ano_lancamento = 'Ano Não Encontrado'
            logging.warning("'summary_content' não encontrada dentro de 'summary_content_wrap'")
    else:
        ano_lancamento = 'Ano Não Encontrado'
        logging.warning("'summary_content_wrap' não encontrada")

    logging.info(f"Ano de Lançamento: {ano_lancamento}")

    # Nota
    post_rating = soup.find('div', class_='post-rating')
    nota_span = post_rating.find('span', class_='score font-meta total_votes')
    nota = nota_span.get_text().strip() if nota_span else '0'
    logging.info(f"Nota: {nota}")

    # Baixar a imagem da capa se a URL estiver disponível
    if poster_url:
        try:
            logging.info("Iniciando download da imagem de capa.")
            img_data = requests.get(poster_url).content
            
            # Verificar o formato da imagem
            img = Image.open(BytesIO(img_data))
            if img.format == 'WEBP':
                img = img.convert("RGB")
                img_extension = 'jpg'
            else:
                img_extension = img.format.lower()
                
            # Limpar o nome do arquivo
            img_name = f"{re.sub(r'[^a-zA-Z0-9_]', '', titulo.replace(' ', '_'))}_cover.{img_extension}"
            img_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'static', 'covers', img_name)  # Usar o diretório existente

            # Criar o diretório se não existir
            os.makedirs(os.path.dirname(img_path), exist_ok=True)

            # Salvar a imagem da capa localmente
            img.save(img_path)
            logging.info(f"Imagem de capa salva com sucesso em {img_path}.")

            # Verificar se o arquivo foi salvo e obter seu tamanho
            if os.path.exists(img_path):
                file_size = os.path.getsize(img_path)
                logging.info(f"Arquivo salvo: {img_path} ({file_size} bytes)")
            else:
                logging.error("Erro: o arquivo da imagem de capa não foi encontrado no diretório.")

        except Exception as e:
            logging.error(f"Erro ao baixar ou salvar a imagem de capa: {e}")
            img_name = None
    else:
        logging.warning("URL da imagem de capa não encontrada.")
        img_name = None

    categoria = ', '.join(categorias)  # Converter lista de categorias em string

    novo_manga = Manga(nome=titulo, descricao=descricao, categoria=categoria, ano_lancamento=ano_lancamento, nota=nota, url_base=url_base, capa=img_name)
    db.session.add(novo_manga)
    db.session.commit()
    
    # Capítulos e URLs
    capitulos_e_urls = []
    sub_chap_list = soup.find('ul', class_='sub-chap-list')
    if sub_chap_list:
        for li in sub_chap_list.find_all('li'):
            capitulo_url = li.find('a')['href'] if li.find('a') else None
            capitulo_text = li.find('a').get_text().strip() if li.find('a') else 'Número Não Encontrado'
            numero_capitulo = capitulo_text.replace('Capítulo', '').strip()
            logging.info(f"Capítulo: {numero_capitulo}, URL: {capitulo_url}")
            capitulos_e_urls.append((numero_capitulo, capitulo_url))
    else:
        logging.error("UL 'sub-chap-list' não encontrada.")

    # Garantir que capitulos_e_urls esteja sempre definida
    if not capitulos_e_urls:
        logging.warning("Nenhum capítulo encontrado, adicionando valor padrão 'SEM URL'.")
        capitulos_e_urls = [("1", "SEM URL")]

    return capitulos_e_urls, novo_manga.id, titulo, categorias












@routes.route('/process_chapter', methods=['POST'])
@login_required
def processar_capitulo_route():
    chapter_url = request.form.get('chapter_url')
    chapter_number = request.form.get('chapter_number')
    manga_id = request.form.get('manga_id')
    nome_manga = request.form.get('nome_manga')
    fonte = request.form.get('fonte')
    url_tratada = chapter_url.rsplit('-', 1)[0] + '-'

    print(f"FONTE: {fonte}")
    # Verificar se é uma fonte específica e chamar a função correspondente
    if fonte == '2':
        processar_capitulos_fonte_2(url_tratada, float(chapter_number), float(chapter_number), manga_id, nome_manga)
    elif fonte == '1':
        processar_capitulos(url_tratada, float(chapter_number), float(chapter_number), manga_id, nome_manga)
    else:
        return jsonify({'error': 'Fonte inválida'}), 400

    return jsonify(success=True)


@routes.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    manga = Manga.query.get_or_404(id)
    if request.method == 'POST':
        manga.nome = request.form['nome']
        manga.descricao = request.form['descricao']
        
        # Remover duplicatas das categorias antes de salvar
        categorias = request.form['categoria'].split(',')
        manga.categoria = ', '.join(list(set([c.strip() for c in categorias])))

        manga.url_base = request.form['url_base']
        manga.ano_lancamento = request.form['ano_lancamento']
        manga.nota = request.form['nota']
        capa = request.files['capa']
        
        # Salvar a nova imagem da capa, se houver
        if capa and capa.filename != '':
            capa_filename = f"{manga.nome.replace(' ', '_')}_cover.jpg"
            capa_path = os.path.join('static', 'covers', capa_filename)
            os.makedirs(os.path.dirname(capa_path), exist_ok=True)
            capa.save(capa_path)
            manga.capa = capa_filename
        
        db.session.commit()
        return redirect(url_for('routes.listar_mangas'))
    
    # Remover duplicatas das categorias antes de renderizar o template
    categorias_unicas = list(set(manga.categoria.split(', ')))
    print(f"Categorias carregadas do banco de dados (únicas): {categorias_unicas}")  # Adicionar o print
    categorias_unicas_str = ', '.join(categorias_unicas)
    return render_template('edit.html', manga=manga, categorias=categorias_unicas_str)





@routes.route('/listar_mangas')
@login_required
def listar_mangas():
    query = request.args.get('query')
    page = request.args.get(get_page_parameter(), type=int, default=1)
    if query:
        mangas_query = Manga.query.filter(Manga.nome.like(f'%{query}%')).order_by(Manga.data_adicao.desc())
    else:
        mangas_query = Manga.query.order_by(Manga.data_adicao.desc())

    total = mangas_query.count()
    mangas = mangas_query.paginate(page=page, per_page=9).items
    pagination = Pagination(page=page, total=total, search=query, record_name='mangas', per_page=9, css_framework='bootstrap4')
    
    return render_template('listar_mangas.html', mangas=mangas, query=query, pagination=pagination)


@routes.route('/delete_manga/<int:id>', methods=['POST'])
@login_required
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
@login_required
def capitulos():
    query = request.args.get('query')
    page = request.args.get(get_page_parameter(), type=int, default=1)
    if query:
        capitulos_query = Capitulo.query.filter(Capitulo.numero.like(f'%{query}%')).order_by(Capitulo.data_cadastro.desc())
    else:
        capitulos_query = Capitulo.query.order_by(Capitulo.data_cadastro.desc())

    total = capitulos_query.count()
    capitulos = capitulos_query.paginate(page=page, per_page=9).items
    pagination = Pagination(page=page, total=total, search=query, record_name='capitulos', per_page=9, css_framework='bootstrap4')
    
    return render_template('capitulos.html', capitulos=capitulos, query=query, pagination=pagination)
import logging

# Configurar o logger
logging.basicConfig(level=logging.INFO)

@routes.route('/add_chapter/<int:id>', methods=['GET', 'POST'])
@login_required
def add_chapter(id):
    manga = Manga.query.get_or_404(id)
    if request.method == 'POST':
        numero_capitulo = request.form['numero_capitulo']
        url_base = request.form['url_base']
        fonte = request.form['fonte']  # Capturar o valor da fonte
        pdf_capitulo = request.files.get('pdf_capitulo')

        try:
            if pdf_capitulo and pdf_capitulo.filename != '':
                # Salvar o PDF manualmente
                pdf_filename = f"{manga.nome.replace(' ', '_')}_capitulo_{numero_capitulo}.pdf"
                pdf_path = os.path.join('static', 'pdfs', pdf_filename)
                os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
                pdf_capitulo.save(pdf_path)
                logging.info(f"PDF carregado manualmente: {pdf_filename}")
                logging.info(f"URL do PDF: /static/pdfs/{pdf_filename}")

                # Adicionar o capítulo ao banco de dados
                novo_capitulo = Capitulo(manga_id=manga.id, numero=numero_capitulo, arquivo_pdf=f"pdfs/{pdf_filename}")
                db.session.add(novo_capitulo)
                db.session.commit()
            else:
                # Lógica para processar o capítulo usando a URL Base e a Fonte
                if fonte == '2':
                    processar_capitulos_fonte_2(url_base, float(numero_capitulo), float(numero_capitulo), manga.id, manga.nome)
                elif fonte == '1':
                    processar_capitulos(url_base, float(numero_capitulo), float(numero_capitulo), manga.id, manga.nome)
                else:
                    return jsonify({'success': False, 'message': 'Fonte inválida.'})

            return jsonify({'success': True, 'message': 'Capítulo adicionado com sucesso.'})
        except Exception as e:
            logging.error(f"Erro ao processar o capítulo {numero_capitulo}: {e}")
            return jsonify({'success': False, 'message': 'Erro ao adicionar capítulo.'})

    return render_template('add_chapter.html', manga=manga)





@routes.route('/edit_capitulo/<int:id>', methods=['GET', 'POST'])
@login_required
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
@login_required
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


@routes.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        is_admin = 'is_admin' in request.form  # Ajuste para verificar o checkbox
        
        # Verificar se o usuário ou email já existe
        if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
            flash('Usuário ou email já existe!', 'danger')
        else:
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')  # Hash da senha
            user = User(username=username, email=email, password=hashed_password, is_admin=is_admin)
            db.session.add(user)
            db.session.commit()
            flash('Usuário cadastrado com sucesso!', 'success')
    
    return render_template('register.html')

@routes.route('/users', methods=['GET', 'POST'])
@login_required
def list_users():
    search_query = request.form.get('search_query', '')
    if search_query:
        users = User.query.filter(User.username.contains(search_query) | User.email.contains(search_query)).all()
    else:
        users = User.query.all()
    return render_template('list_users.html', users=users, search_query=search_query)


@routes.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('Usuário excluído com sucesso!', 'success')
    return redirect(url_for('routes.list_users'))



@routes.route('/inicial')
def inicial():
    return render_template('inicial.html')

@routes.route('/api/mangas_recentes', methods=['GET'])
def mangas_recentes():
    mangas = Manga.query.order_by(Manga.data_adicao.desc()).limit(10).all()
    mangas_data = [{'id':manga.id,'nome': manga.nome, 'capa': manga.capa, 'data_adicao': manga.data_adicao} for manga in mangas]
    return jsonify({'mangas': mangas_data})

@routes.route('/api/capitulos_recentes', methods=['GET'])
def capitulos_recentes():
    capitulos = Capitulo.query.order_by(Capitulo.data_cadastro.desc()).limit(12).all()
    capitulos_data = [{'id': capitulo.id, 'numero': capitulo.numero, 'manga_id': capitulo.manga_id, 'manga_nome': capitulo.manga.nome, 'manga_capa': capitulo.manga.capa, 'data_cadastro': capitulo.data_cadastro} for capitulo in capitulos]
    return jsonify({'capitulos': capitulos_data})





@routes.route('/detalhes/<int:manga_id>')
def detalhes(manga_id):
    manga = Manga.query.get_or_404(manga_id)
    # Ordenar capítulos numericamente do maior para o menor
    manga.capitulos = sorted(manga.capitulos, key=lambda capitulo: float(capitulo.numero), reverse=True)
    return render_template('detalhes.html', manga=manga)



@routes.route('/api/detalhes/<int:manga_id>')
def api_detalhes(manga_id):
    manga = Manga.query.get_or_404(manga_id)
    # Ordenar capítulos numericamente do maior para o menor
    manga.capitulos = sorted(manga.capitulos, key=lambda capitulo: float(capitulo.numero), reverse=True)
    manga_dict = {
        'capa': manga.capa,
        'nome': manga.nome,
        'descricao': manga.descricao,
        'ano_lancamento': manga.ano_lancamento,
        'nota': manga.nota,
        'categoria': manga.categoria,
        'capitulos': [{'numero': capitulo.numero, 'data_cadastro': capitulo.data_cadastro.isoformat()} for capitulo in manga.capitulos]
    }
    return jsonify(manga_dict)


@routes.route('/api/ultimos_mangas', methods=['GET'])
def ultimos_mangas():
    mangas = Manga.query.order_by(Manga.data_adicao.desc()).limit(5).all()
    mangas_data = [{'id': manga.id, 'nome': manga.nome, 'capa': manga.capa, 'data_adicao': manga.data_adicao, 'nota': manga.nota} for manga in mangas]
    return jsonify({'mangas': mangas_data})


from sqlalchemy import or_


# Função para filtrar mangás por letra
def filtrar_mangas_por_letra(letra):
    if letra == "#-1":
        return Manga.query.filter(or_(Manga.nome.ilike('[0-9]%'), Manga.nome.ilike('[!@#$%^&*()-_=+{};:,<.>/?~`]+%')))
    return Manga.query.filter(Manga.nome.ilike(f'{letra}%'))

@routes.route('/lista_mangas', methods=['GET'])
def render_lista_mangas():
    return render_template('lista_mangas.html')

@routes.route('/api/lista_mangas', methods=['GET'])
def lista_mangas():
    page = request.args.get('page', 1, type=int)
    letra = request.args.get('letra', '', type=str)
    
    if letra:
        mangas_query = filtrar_mangas_por_letra(letra)
    else:
        mangas_query = Manga.query.order_by(Manga.data_adicao.desc())

    mangas = mangas_query.paginate(page=page, per_page=12)
    mangas_data = [{'id': manga.id, 'nome': manga.nome, 'capa': manga.capa, 'data_adicao': manga.data_adicao} for manga in mangas.items]
    return jsonify({'mangas': mangas_data, 'total_pages': mangas.pages, 'current_page': mangas.page})




@routes.route('/capitulo/<int:manga_id>/<float:capitulo_numero>', methods=['GET'])
def detalhes_capitulo(manga_id, capitulo_numero):
    logging.info(f'Buscando detalhes do capítulo número {capitulo_numero} do mangá com ID: {manga_id}')
    capitulo = Capitulo.query.filter(Capitulo.manga_id == manga_id, Capitulo.numero == capitulo_numero).first()
    if not capitulo:
        logging.error(f'Capítulo número {capitulo_numero} do mangá com ID {manga_id} não encontrado.')
        return "Capítulo não encontrado", 404

    manga = Manga.query.get(manga_id)
    if not manga:
        logging.error(f'Mangá com ID {manga_id} não encontrado.')
        return "Mangá não encontrado", 404

    # Obtendo o capítulo anterior e próximo
    capitulo_anterior = Capitulo.query.filter(Capitulo.manga_id == manga_id, Capitulo.numero == capitulo_numero - 1).first()
    capitulo_proximo = Capitulo.query.filter(Capitulo.manga_id == manga_id, Capitulo.numero == capitulo_numero + 1).first()

    # Adicionando logs para os capítulos anterior e próximo
    if capitulo_anterior:
        logging.info(f'Capítulo anterior encontrado com número: {capitulo_anterior.numero}')
    else:
        logging.info('Capítulo anterior não encontrado.')

    if capitulo_proximo:
        logging.info(f'Próximo capítulo encontrado com número: {capitulo_proximo.numero}')
    else:
        logging.info('Próximo capítulo não encontrado.')

    # Definindo os números dos capítulos anterior e próximo
    capitulo.anterior_numero = capitulo_anterior.numero if capitulo_anterior else None
    capitulo.proximo_numero = capitulo_proximo.numero if capitulo_proximo else None

    logging.info(f'Detalhes do capítulo número {capitulo_numero} encontrados. Renderizando página com anteriores: {capitulo.anterior_numero} e próximos: {capitulo.proximo_numero}.')
    return render_template('detalhes_capitulo.html', capitulo=capitulo, manga=manga)


@routes.route('/lista_capitulos', methods=['GET'])
def lista_capitulos():
    return render_template('lista_capitulos.html')

import math
import logging

@routes.route('/api/ultimos_capitulos', methods=['GET'])
def ultimos_capitulos():
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 12, type=int)
    offset = (page - 1) * limit

    capitulos_query = Capitulo.query.order_by(Capitulo.data_cadastro.desc())
    total_capitulos = capitulos_query.count()
    capitulos = capitulos_query.offset(offset).limit(limit).all()

    capitulos_data = [{'id': capitulo.id, 'numero': capitulo.numero, 'manga_id': capitulo.manga_id, 'manga_nome': capitulo.manga.nome, 'manga_capa': capitulo.manga.capa, 'data_cadastro': capitulo.data_cadastro} for capitulo in capitulos]

    total_pages = math.ceil(total_capitulos / limit)

    return jsonify({
        'capitulos': capitulos_data,
        'total_pages': total_pages,
        'current_page': page
    })

@routes.route('/api/sugestoes_pesquisa', methods=['GET'])
def sugestoes_pesquisa():
    termo = request.args.get('termo', '', type=str)
    if termo:
        mangas = Manga.query.filter(Manga.nome.ilike(f'%{termo}%')).limit(10).all()
        mangas_data = [{'id': manga.id, 'nome': manga.nome, 'capa': manga.capa} for manga in mangas]
        return jsonify({'mangas': mangas_data})
    return jsonify({'mangas': []})