document.addEventListener('DOMContentLoaded', function () {
    // Initialize TomSelect for Table Materials
    document.querySelectorAll('.ts-select-table').forEach((el) => {
        new TomSelect(el, {
            selectOnTab: true,
            create: false, // Forces selection from the list ONLY
            placeholder: "Search material...",
            maxOptions: 50, // Helps with performance if the list is huge
            dropdownParent: 'body', // Fixes overflow issues in scrolling tables
            onItemAdd: function() {
                this.blur(); // Close dropdown after selection
            }
        });
    });
    
    // ... rest of your weight calculation logic ...
});