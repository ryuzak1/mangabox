document.addEventListener('DOMContentLoaded', function() {
    // Função para inverter a ordem dos capítulos
    function toggleChapterOrder() {
        const chapterList = document.getElementById('manga-chapters-list');
        const chapters = Array.from(chapterList.children);
        chapters.reverse().forEach(chapter => chapterList.appendChild(chapter));
    }

    // Adicionar evento de clique ao botão de inverter ordem
    document.getElementById('toggle-order-btn').addEventListener('click', toggleChapterOrder);

    // Mock data for manga details
    const manga = {
        capa: 'https://example.com/path-to-cover.jpg',
        nome: 'Martial Peak',
        descricao: 'Ler o Mangá Martial Peak Online em Português PT-BR...',
        ano_lancamento: 2018,
        nota: 9.2,
        categorias: 'Ação, Artes Marciais, Aventura, Comédia, Fantasia, Harém, Histórico, M, Romance, Sobrenatural, Webtoon',
        capitulos: [
            { numero: 3185, data_cadastro: '2023-04-06' },
            { numero: 3184, data_cadastro: '2023-04-06' },
            { numero: 3183, data_cadastro: '2023-04-06' },
        ]
    };

    // Preencher os detalhes do mangá
    document.getElementById('manga-cover').src = manga.capa;
    document.getElementById('manga-title').textContent = manga.nome;
    document.getElementById('manga-description').textContent = manga.descricao;
    document.getElementById('manga-year').textContent = manga.ano_lancamento;
    document.getElementById('manga-rating').textContent = manga.nota;
    document.getElementById('manga-categories').textContent = manga.categorias;

    // Preencher a lista de capítulos
    const chaptersList = document.getElementById('manga-chapters-list');
    manga.capitulos.sort((a, b) => b.numero - a.numero).forEach(chapter => {
        const listItem = document.createElement('li');
        listItem.className = 'list-group-item';
        listItem.textContent = `Capítulo ${chapter.numero} - ${new Date(chapter.data_cadastro).toLocaleDateString()}`;
        chaptersList.appendChild(listItem);
    });
});
