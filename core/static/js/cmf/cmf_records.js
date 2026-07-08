document.addEventListener('DOMContentLoaded', function() {
    const completedCheckbox = document.getElementById('completed');
    const pendingCheckbox = document.getElementById('pending');
    const modeToggle = document.getElementById('modeToggle');
    const refreshBtn = document.getElementById('refreshBtn');

    function reloadWithParams() {
        const params = new URLSearchParams({
            mode: modeToggle.checked ? 'rs' : 'cmf',
            completed: completedCheckbox.checked ? '1' : '0',
            pending: pendingCheckbox.checked ? '1' : '0',
        });
        window.location.href = `${window.location.pathname}?${params.toString()}`;
    }

    completedCheckbox.addEventListener('change', reloadWithParams);
    pendingCheckbox.addEventListener('change', reloadWithParams);
    modeToggle.addEventListener('change', reloadWithParams);
    refreshBtn.addEventListener('click', reloadWithParams);
});