document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.ts-select').forEach((el) => {
        new TomSelect(el, {
            create: false, // Disallow user to add new items (Strict validation)
            controlInput: '<input />',
            render:{
                option:function(data,escape){
                    return '<div class="extra-small">' + escape(data.text) + '</div>';
                },
                item:function(data,escape){
                    return '<div class="extra-small">' + escape(data.text) + '</div>';
                }
            }
        });
    });
});