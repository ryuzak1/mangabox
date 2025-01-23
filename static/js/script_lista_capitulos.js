document.addEventListener('DOMContentLoaded', function() {
    const urlParams = new URLSearchParams(window.location.search);
    let page = parseInt(urlParams.get('page')) || 1;

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

    // Função para carregar os capítulos
    function loadChapters(page) {
        fetch(`/api/ultimos_capitulos?page=${page}`)
            .then(response => response.json())
            .then(data => {
                const chapterRow = document.getElementById('chapterRow');
                chapterRow.innerHTML = '';
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

                // Paginação
                const pagination = document.getElementById('pagination');
                pagination.innerHTML = '';
                for (let i = 1; i <= data.total_pages; i++) {
                    const pageItem = document.createElement('li');
                    pageItem.className = `page-item ${i === data.current_page ? 'active' : ''}`;
                    pageItem.innerHTML = `<a class="page-link" href="?page=${i}">${i}</a>`;
                    pagination.appendChild(pageItem);
                }
            })
            .catch(error => console.error('Erro ao carregar os capítulos:', error));
    }

    // Carregar últimos 5 mangás adicionados
    function loadLatestMangas() {
        fetch('/api/ultimos_mangas')
            .then(response => response.json())
            .then(data => {
                const latestMangasList = document.getElementById('latestMangasList');
                latestMangasList.innerHTML = '';
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
            .catch(error => console.error('Erro ao carregar os últimos mangás adicionados:', error));
    }

    loadChapters(page);
    loadLatestMangas();
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
