document.addEventListener('DOMContentLoaded', function() {
    // --- TOM SELECT INITIALIZATION (Reusable) ---
    // This looks for every element with 'ts-select' and turns it into a searchable tag-box
    document.querySelectorAll('.ts-select').forEach((el) => {
        new TomSelect(el, {
            plugins: ['remove_button'], // Allows clicking 'x' to remove items
            create: false,
            persist: false,
            placeholder: el.getAttribute('placeholder') || "Select options...",
            maxOptions: null,
            // Optimization for the tag look
            onItemAdd: function() {
                this.setTextboxValue('');
                this.refreshOptions();
            }
        });
    });

    // --- YOUR EXISTING PARAMS LOGIC ---
    const completedCheckbox = document.getElementById('completed');
    const pendingCheckbox = document.getElementById('pending');
    const modeToggle = document.getElementById('modeToggle');
    const refreshBtn = document.getElementById('refreshBtn');

    function reloadWithParams() {
        // We only try to reload if the elements actually exist on the current page
        if (!completedCheckbox || !pendingCheckbox || !modeToggle) return;

        const params = new URLSearchParams({
            mode: modeToggle.checked ? 'rs' : 'cmf',
            completed: completedCheckbox.checked ? '1' : '0',
            pending: pendingCheckbox.checked ? '1' : '0',
        });
        window.location.href = `${window.location.pathname}?${params.toString()}`;
    }

    if (completedCheckbox) completedCheckbox.addEventListener('change', reloadWithParams);
    if (pendingCheckbox) pendingCheckbox.addEventListener('change', reloadWithParams);
    if (modeToggle) modeToggle.addEventListener('change', reloadWithParams);
    if (refreshBtn) refreshBtn.addEventListener('click', reloadWithParams);
});