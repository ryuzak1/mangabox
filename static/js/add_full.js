$(document).ready(function() {
    $('#mangaForm').on('submit', function(event) {
        event.preventDefault();
        const urlBase = $('#url_base').val();
        $('#progress-container').show();

        $.ajax({
            type: 'POST',
            url: $('#mangaForm').attr('action'),
            data: { url_base: urlBase },
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
                $.ajax({
                    type: 'POST',
                    url: '/process_chapter',
                    data: { chapter_url: chapter.url, chapter_number: chapter.number, manga_id: chapter.manga_id, nome_manga: chapter.nome_manga },
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
