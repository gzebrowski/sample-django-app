;
(function($) {
    $(document).ready(function() {
        if ($('.app-indexer.model-workingtask.change-list').length) {
            setInterval(function() { 
                if ($('.action-checkbox input[type=checkbox]:checked').length || $('.status-all.status-s0, .status-all.status-s1, .status-all.status-s3, .status-all.status-s7').length == 0) {
                    return;
                }
                location.href = location.href.split('#')[0]; }, 7000);
        }
        $('.field-work_type input[type=radio]').click(function() {
            var val = $(this).val();
            $('.field-extra_options').find('input[name=extra_options]').each(function() {
                $(this).closest('label').closest('li, div, span').toggle(($(this).val().indexOf(val + ':') == 0)); 
            });
        });
        $('.field-extra_options').find('input[name=extra_options]').each(function() {
            $(this).closest('label').closest('li, div, span').hide();
        });
    });
})(django.jQuery);
