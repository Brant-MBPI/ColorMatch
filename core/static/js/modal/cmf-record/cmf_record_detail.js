document.addEventListener('DOMContentLoaded', function () {
    const recordsTbody = document.getElementById('recordsTbody');
    const modalElement = document.getElementById('cmfDetailModal');
    if (!modalElement || !recordsTbody) return;

    const modalTableBody = document.getElementById('modalTableBody');
    const bsModal = new bootstrap.Modal(modalElement);

    // --- 1. DOUBLE CLICK TRIGGER: Background Fetch (No Redirect) ---
    recordsTbody.addEventListener('dblclick', async function (e) {
        const tr = e.target.closest('.record-row');
        if (!tr) return;

        const cmfNo = tr.cells[0].innerText.trim();
        
        // Show loader inside modal and show modal
        modalTableBody.innerHTML = '<tr><td colspan="7" class="text-center py-5"><div class="spinner-border text-teal spinner-border-sm"></div> Fetching data...</td></tr>';
        bsModal.show();

        try {
            // URL must match your urls.py path for cmf_record_detail
            const response = await fetch(`/cmf/records/${encodeURIComponent(cmfNo)}/`);
            const htmlSnippet = await response.text();
            
            // Inject the Python-rendered partial into the modal table body
            modalTableBody.innerHTML = htmlSnippet;
        } catch (error) {
            console.error('Fetch Error:', error);
            modalTableBody.innerHTML = '<tr><td colspan="7" class="text-center py-4 text-danger">Error fetching database records.</td></tr>';
        }
    });

    // --- 2. MODAL INTERACTION LOGIC (Click to Expand) ---
    modalTableBody.addEventListener('click', function (e) {
        // A. Toggle Main Parent Row (CMF Record detail)
        const parentRow = e.target.closest('.main-modal-parent-row');
        if (parentRow) {
            const formulaRow = parentRow.nextElementSibling;
            const icon = parentRow.querySelector('.toggle-main-icon');
            const isHidden = formulaRow.classList.toggle('d-none');
            
            // Toggle icon visual
            icon.className = isHidden ? 'bi bi-plus-circle-fill toggle-main-icon' : 'bi bi-dash-circle-fill toggle-main-icon text-danger';
            return;
        }

        // B. Toggle Internal Formula Headers (Show Ingredients)
        const formulaHeader = e.target.closest('.formula-header-clickable');
        if (formulaHeader) {
            const ingredientRow = formulaHeader.nextElementSibling;
            ingredientRow.classList.toggle('d-none');
            
            // Highlight the header while expanded
            if (!ingredientRow.classList.contains('d-none')) {
                formulaHeader.style.backgroundColor = 'var(--sidebar-hover-bg)';
            } else {
                formulaHeader.style.backgroundColor = '';
            }
        }
    });
});