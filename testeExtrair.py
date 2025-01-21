import requests
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
from fpdf import FPDF

# Função para obter todas as URLs das imagens dentro das divs específicas, com logs
def get_image_urls(url):
    print(f'Acessando URL: {url}')
    response = requests.get(url)
    print(f'Resposta HTTP: {response.status_code}')
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Navega pela estrutura até encontrar a div com a classe reading-content
    site_content = soup.find('div', class_='site-content')
    if not site_content:
        print('Não encontrou a div com a classe site-content')
        return []

    reading_content_wrap = site_content.find('div', class_='reading-content-wrap')
    if not reading_content_wrap:
        print('Não encontrou a div com a classe reading-content-wrap')
        return []

    content_area = reading_content_wrap.find('div', class_='content-area')
    if not content_area:
        print('Não encontrou a div com a classe content-area')
        return []

    container = content_area.find('div', class_='container')
    if not container:
        print('Não encontrou a div com a classe container')
        return []

    row_flex = container.find('div', class_='row')
    if not row_flex:
        print('Não encontrou a div com a classe row')
        return []

    main_col = row_flex.find('div', class_='main-col')
    if not main_col:
        print('Não encontrou a div com a classe main-col')
        return []

    main_col_inner = main_col.find('div', class_='main-col-inner')
    if not main_col_inner:
        print('Não encontrou a div com a classe main-col-inner')
        return []

    c_blog_post = main_col_inner.find('div', class_='c-blog-post')
    if not c_blog_post:
        print('Não encontrou a div com a classe c-blog-post')
        return []

    entry_content = c_blog_post.find('div', class_='entry-content')
    if not entry_content:
        print('Não encontrou a div com a classe entry-content')
        return []

    entry_content_wrap = entry_content.find('div', class_='entry-content_wrap')
    if not entry_content_wrap:
        print('Não encontrou a div com a classe entry-content_wrap')
        return []

    read_container = entry_content_wrap.find('div', class_='read-container')
    if not read_container:
        print('Não encontrou a div com a classe read-container')
        return []

    reading_content = read_container.find('div', class_='reading-content')
    if reading_content:
        print('Encontrou a div com a classe reading-content')
    else:
        print('Não encontrou a div com a classe reading-content')
        return []

    image_divs = reading_content.find_all('div', class_='page-break')
    print(f'Número de divs com a classe page-break: {len(image_divs)}')
    
    image_urls = []
    for index, div in enumerate(image_divs):
        img_tag = div.find('img')
        if img_tag:
            print(f'Tag img encontrada na div {index + 1}: {img_tag}')
            if img_tag.has_attr('data-src'):
                print(f'Conteúdo do data-src na div {index + 1}: {img_tag["data-src"]}')
                image_urls.append(img_tag['data-src'])
                print(f'Adicionou imagem válida na div {index + 1}: {img_tag["data-src"]}')
            else:
                print(f'Tag img na div {index + 1} não possui atributo data-src')
        else:
            print(f'Não encontrou tag img na div {index + 1}')
    
    return image_urls

# Função para baixar as imagens e salvar como PDF usando fpdf
def images_to_pdf(url, output_pdf):
    image_urls = get_image_urls(url)
    
    pdf = FPDF()
    for index, image_url in enumerate(image_urls):
        print(f'Baixando imagem {index + 1} de: {image_url}')
        response = requests.get(image_url)
        img = Image.open(BytesIO(response.content))
        
        # Verifica se a imagem é webp e converte para JPEG temporariamente
        if img.format == 'WEBP':
            img = img.convert("RGB")
        
        # Salva a imagem temporariamente
        temp_image = f'temp_image_{index + 1}.png'
        img.save(temp_image)
        
        # Adiciona a imagem ao PDF
        pdf.add_page()
        pdf.image(temp_image, x=0, y=0, w=210, h=297)
    
    # Salva o arquivo PDF
    pdf.output(output_pdf)

# URL da página e nome do arquivo PDF de saída
page_url = input('Digite a URL da página: ')
output_pdf = 'output.pdf'

# Chama a função para converter as imagens em PDF
images_to_pdf(page_url, output_pdf)

print(f'Imagens extraídas e salvas em {output_pdf}')
