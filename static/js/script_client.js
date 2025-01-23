document.addEventListener('DOMContentLoaded', function() {
    console.log('Script carregado e executado.');

    // Função para exibir sugestões de pesquisa
    function showSuggestions(termo) {
        if (termo.length === 0) {
            document.getElementById('suggestions').innerHTML = '';
            return;
        }
        fetch(`/api/sugestoes_pesquisa?termo=${termo}`)
            .then(response => response.json())
            .then(data => {
                const suggestions = document.getElementById('suggestions');
                suggestions.innerHTML = '';
                data.mangas.slice(0, 3).forEach(manga => {
                    const suggestionItem = document.createElement('a');
                    suggestionItem.href = `/detalhes/${manga.id}`;
                    suggestionItem.className = 'suggestion-item';
                    suggestionItem.innerHTML = `
                        <img src="/static/covers/${manga.capa}" alt="${manga.nome}" class="suggestion-img">
                        <span class="suggestion-text">${manga.nome}</span>
                    `;
                    suggestions.appendChild(suggestionItem);
                });
            });
    }

    const searchInput = document.getElementById('searchInput');
    searchInput.addEventListener('input', function() {
        const termo = searchInput.value;
        showSuggestions(termo);
    });

    // Função para selecionar letras e navegar para a lista de mangás
    function configurarSelecaoDeLetras() {
        const alphabetButtonsContainer = document.querySelector('.alphabet-buttons');
        if (alphabetButtonsContainer) {
            console.log('Div alphabet-buttons encontrada.');
            const alphabetButtons = alphabetButtonsContainer.querySelectorAll('button');
            console.log(`Número de botões encontrados: ${alphabetButtons.length}`);
            alphabetButtons.forEach(button => {
                console.log(`Botão encontrado: ${button.textContent}`);
                button.addEventListener('click', function() {
                    const letra = this.textContent === "#-1" ? "%23-1" : this.textContent; // Codificar "#-1"
                    console.log(`Letra clicada: ${letra}`);
                    window.location.href = `/lista_mangas?letra=${letra}&page=1`;
                });
            });
        } else {
            console.log('Div alphabet-buttons não encontrada.');
        }
    }

    // Configurar a seleção de letras na página inicial
    configurarSelecaoDeLetras();
    
    // Função para inverter a ordem dos capítulos
    function toggleChapterOrder() {
        const chapterList = document.getElementById('manga-chapters-list');
        const chapters = Array.from(chapterList.children);
        chapters.reverse().forEach(chapter => chapterList.appendChild(chapter));
    }

    // Função para extrair manga_id da URL
    function getMangaIdFromUrl() {
        const urlParts = window.location.pathname.split('/');
        return urlParts[urlParts.length - 1];
    }

    // Carregar dados do backend e preencher os cards e capítulos
    fetch('/api/mangas_recentes')
        .then(response => response.json())
        .then(data => {
            const mangaRow = document.getElementById('mangaRow');
            data.mangas.forEach(manga => {
                const col = document.createElement('div');
                col.className = 'col-md-4 mb-4';
                col.innerHTML = `
                    <div class="card" onclick="window.location.href='/detalhes/${manga.id}'">
                        <img src="/static/covers/${manga.capa}" class="card-img-top" alt="${manga.nome}">
                        <div class="card-body">
                            <h5 class="card-title">${manga.nome}</h5>
                        </div>
                    </div>
                `;
                mangaRow.appendChild(col);
            });
        });

    fetch('/api/capitulos_recentes')
        .then(response => response.json())
        .then(data => {
            const chapterRow = document.getElementById('chapterRow');
            data.capitulos.forEach(capitulo => {
                const col = document.createElement('div');
                col.className = 'col-md-4 mb-4';
                col.innerHTML = `
                    <div class="card" onclick="window.location.href='/capitulo/${capitulo.manga_id}/${capitulo.numero}'">
                        <img src="/static/covers/${capitulo.manga_capa}" class="card-img-top" alt="Capítulo ${capitulo.numero}">
                        <div class="card-body">
                            <h5 class="card-title">Capítulo ${capitulo.numero}</h5>
                            <p class="card-text">${capitulo.manga_nome}</p>
                        </div>
                    </div>
                `;
                chapterRow.appendChild(col);
            });
        });

    fetch('/api/ultimos_mangas')
        .then(response => response.json())
        .then(data => {
            const latestMangasList = document.getElementById('latestMangasList');
            data.mangas.forEach(manga => {
                const listItem = document.createElement('li');
                listItem.className = 'list-group-item d-flex align-items-center';
                listItem.innerHTML = `
                    <a href="/detalhes/${manga.id}" class="d-flex align-items-center">
                        <img src="/static/covers/${manga.capa}" alt="${manga.nome}" style="width: 50px; height: 75px; margin-right: 10px;">
                        <div>
                            <p style="margin: 0;">${manga.nome}</p>
                            <p style="margin: 0;"><i class="fas fa-star" style="color: yellow;"></i> ${manga.nota}</p>
                        </div>
                    </a>
                `;
                latestMangasList.appendChild(listItem);
            });
        })
        .catch(error => console.error('Erro ao buscar os últimos mangás adicionados:', error));

    const mangaId = getMangaIdFromUrl();
    fetch(`/api/detalhes/${mangaId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Erro ao buscar os detalhes do mangá.');
            }
            return response.json();
        })
        .then(manga => {
            document.getElementById('manga-cover').src = `/static/covers/${manga.capa}`;
            document.getElementById('manga-title').textContent = manga.nome;
            document.getElementById('manga-description').textContent = manga.descricao;
            document.getElementById('manga-year').textContent = manga.ano_lancamento;
            document.getElementById('manga-rating').textContent = manga.nota;
            document.getElementById('manga-categories').textContent = manga.categoria;

            const chaptersList = document.getElementById('manga-chapters-list');
            manga.capitulos.forEach(chapter => {
                const listItem = document.createElement('li');
                listItem.className = 'list-group-item';
                listItem.textContent = `Capítulo ${chapter.numero} - ${new Date(chapter.data_cadastro).toLocaleDateString()}`;
                chaptersList.appendChild(listItem);
            });

            console.log('Ordem inicial dos capítulos:', manga.capitulos.map(chapter => chapter.numero));
        });

    // Evento de clique nas letras do alfabeto
    const alphabetButtonsContainer = document.querySelector('.alphabet-buttons');
    if (alphabetButtonsContainer) {
        const alphabetButtons = alphabetButtonsContainer.querySelectorAll('button');
        alphabetButtons.forEach(button => {
            button.addEventListener('click', function() {
                const letra = this.textContent === "#-1" ? "%23-1" : this.textContent; // Codificar "#-1"
                window.location.href = `/lista_mangas?letra=${letra}&page=1`;
            });
        });
    }
});
