document.addEventListener('DOMContentLoaded', function() {
    const prevChapterBtn = document.getElementById('prevChapter');
    const nextChapterBtn = document.getElementById('nextChapter');

    // Logs para verificar os valores dos links
    console.log('Link do capítulo anterior:', prevChapterBtn.href);
    console.log('Link do próximo capítulo:', nextChapterBtn.href);

    // Desabilitar botão de capítulo anterior se número do capítulo anterior for null
    if (prevChapterBtn.classList.contains('disabled')) {
        prevChapterBtn.setAttribute('href', '#');
        prevChapterBtn.setAttribute('aria-disabled', 'true');
    }

    // Desabilitar botão de próximo capítulo se número do capítulo próximo for null
    if (nextChapterBtn.classList.contains('disabled')) {
        nextChapterBtn.setAttribute('href', '#');
        nextChapterBtn.setAttribute('aria-disabled', 'true');
    }
    
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
});
