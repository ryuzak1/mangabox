$(document).ready(function() {
    $('#mangaForm').on('submit', function(event) {
        event.preventDefault();
        const urlBase = $('#url_base').val();
        const fonte = $('#fonte').val(); // Adicionar a seleção de fonte
        $('#progress-container').show();

        $.ajax({
            type: 'POST',
            url: $('#mangaForm').attr('action'),
            data: { url_base: urlBase, fonte: fonte }, // Enviar a fonte junto com a URL base
            success: function(response) {
                const totalChapters = response.total_chapters;
                $('#total-count').text(totalChapters);
                processChapters(response.chapters);
            }
        });
    });

    function processChapters(chapters) {
        let processedCount = 0;

        function processNext() {
            if (processedCount < chapters.length) {
                const chapter = chapters[processedCount];
                const fonte = $('#fonte').val();
                $.ajax({
                    type: 'POST',
                    url: '/process_chapter',
                    data: { chapter_url: chapter.url, chapter_number: chapter.number, manga_id: chapter.manga_id, nome_manga: chapter.nome_manga, fonte: fonte },
                    success: function() {
                        processedCount++;
                        $('#progress-count').text(processedCount);
                        const percentComplete = (processedCount / chapters.length) * 100;
                        $('#progress-bar').css('width', percentComplete + '%').attr('aria-valuenow', percentComplete);

                        if (processedCount === chapters.length) {
                            $('#progress-bar').removeClass('progress-bar-animated').addClass('bg-success').text('Concluído!');
                        } else {
                            processNext();
                        }
                    }
                });
            }
        }

        processNext();
    }
});
