// Simple Search Filter
document.getElementById('feedbackSearch').addEventListener('input', function(e) {
    const term = e.target.value.toLowerCase();
    const rows = document.querySelectorAll('#feedbackTable tbody tr.record-row');

    rows.forEach(row => {
        const text = row.innerText.toLowerCase();
        row.style.display = text.includes(term) ? '' : 'none';
    });
});

// Double-click a row → reload the page with ?id=, which the view
// uses to both pre-fill the Entry tab and switch to it automatically.
document.querySelectorAll('#feedbackTable tbody tr.record-row').forEach(row => {
    row.addEventListener('dblclick', function () {
        const feedbackNo = row.cells[0].innerText.trim();
        window.location.href = `${window.location.pathname}?feedback_no=${encodeURIComponent(feedbackNo)}`;
    });
});