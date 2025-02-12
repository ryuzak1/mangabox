document.addEventListener('DOMContentLoaded', function() {
    // Função para inverter a ordem dos capítulos
    function toggleChapterOrder() {
        const chapterList = document.getElementById('manga-chapters-list');
        const chapters = Array.from(chapterList.children);
        chapters.reverse().forEach(chapter => chapterList.appendChild(chapter));
    }

    // Adicionar evento de clique ao botão de inverter ordem
    document.getElementById('toggle-order-icon').addEventListener('click', toggleChapterOrder);

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

    // Adicionar evento de clique em cada item da lista de capítulos
    const chaptersList = document.getElementById('manga-chapters-list');
    const chapters = Array.from(chaptersList.children);
    chapters.forEach((chapter, index) => {
        chapter.style.cursor = 'pointer'; // Adicionar efeito de mão no cursor
        chapter.addEventListener('click', function() {
            const chapterNumber = chapter.textContent.match(/Capítulo (\d+(\.\d+)?)/)[1];
            const mangaId = window.location.pathname.split('/').pop();
            console.log(`Capítulo clicado: ${chapterNumber}`);
            window.location.href = `/capitulo/${mangaId}/${chapterNumber}`;
        });
    });
});
