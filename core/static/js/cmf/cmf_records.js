document.addEventListener('DOMContentLoaded', function() {

    // --- DOM ELEMENTS ---
    const completedCheckbox = document.getElementById('completed');
    const pendingCheckbox = document.getElementById('pending');
    const modeToggle = document.getElementById('modeToggle');
    const refreshBtn = document.getElementById('refreshBtn');
    const searchInput = document.getElementById('recordSearchInput');
    const searchFieldSelect = document.getElementById('searchFieldSelect');
    const modeLabelCmf = document.getElementById('modeLabelCmf');
    const modeLabelRs = document.getElementById('modeLabelRs');
    const tableHeaderNo = document.getElementById('tableHeaderNo');
    const optNoLabel = document.getElementById('optNoLabel');
    const recordCounter = document.getElementById('recordCounter');
    const contextMenu = document.getElementById('customContextMenu');
    const menuTitle = document.getElementById('contextMenuTitle');
    const recordsTbody = document.getElementById('recordsTbody');

    const COLS_BOTH = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 13];
    const COLS_COMPLETED = [0, 1, 2, 3, 4, 7, 8, 10, 11];
    const COLS_PENDING = [0, 1, 2, 3, 4, 5, 6, 7, 12];

    function applyFilters() {
        const isRsMode = modeToggle ? modeToggle.checked : false;
        const currentMode = isRsMode ? 'rs' : 'cmf';
        const showCompleted = completedCheckbox ? completedCheckbox.checked : true;
        const showPending = pendingCheckbox ? pendingCheckbox.checked : true;
        const searchTerm = searchInput ? searchInput.value.trim().toLowerCase() : '';
        const searchColIndex = searchFieldSelect ? searchFieldSelect.value : 'all';

        if (isRsMode) {
            modeLabelCmf.className = "extra-small fw-bold text-muted";
            modeLabelRs.className = "extra-small fw-bold text-teal";
            tableHeaderNo.textContent = "RS No.";
            if (optNoLabel) optNoLabel.textContent = "RS No.";
        } else {
            modeLabelCmf.className = "extra-small fw-bold text-teal";
            modeLabelRs.className = "extra-small fw-bold text-muted";
            tableHeaderNo.textContent = "CMF No.";
            if (optNoLabel) optNoLabel.textContent = "CMF No.";
        }

        let activeCols = showCompleted && showPending ? COLS_BOTH : (showCompleted ? COLS_COMPLETED : COLS_PENDING);

        for (let i = 0; i <= 12; i++) {
            const isVisible = activeCols.includes(i);
            document.querySelectorAll(`[data-col-index="${i}"]`).forEach(cell => {
                cell.style.display = isVisible ? '' : 'none';
            });
        }

        let visibleCount = 0;
        document.querySelectorAll('.record-row').forEach(row => {
            const matchesMode = row.dataset.mode === currentMode;
            let matchesStatus = (showCompleted && row.dataset.status === 'Completed') || (showPending && row.dataset.status === 'Pending');
            let matchesSearch = searchTerm === '' || (searchColIndex === 'all' ? row.textContent.toLowerCase().includes(searchTerm) : row.querySelector(`[data-col-index="${searchColIndex}"]`).textContent.toLowerCase().includes(searchTerm));

            if (matchesMode && matchesStatus && matchesSearch) {
                row.style.display = '';
                visibleCount++;
            } else {
                row.style.display = 'none';
            }
        });
        if (recordCounter) recordCounter.textContent = `Showing ${visibleCount} records`;
    }

    // --- CONTEXT MENU (Right Click) ---
    if (recordsTbody && contextMenu) {
        recordsTbody.addEventListener('contextmenu', function (e) {
            const tr = e.target.closest('.record-row');
            if (!tr) return;
            e.preventDefault();
            const cmfNo = tr.cells[0].innerText.trim();
            menuTitle.innerText = cmfNo;
            document.getElementById('linkCmfEntry').href = `/cmf/entry/?no=${encodeURIComponent(cmfNo)}`;
            document.getElementById('linkMbFormula').href = `/cmf/mb-formula/?no=${encodeURIComponent(cmfNo)}`;
            document.getElementById('linkDcFormula').href = `/cmf/dc-formula/?no=${encodeURIComponent(cmfNo)}`;
            document.getElementById('linkPendingCompleted').href = `/cmf/pending-completed/?no=${encodeURIComponent(cmfNo)}`;

            contextMenu.style.top = `${e.clientY}px`;
            contextMenu.style.left = `${e.clientX}px`;
            contextMenu.style.display = 'block';
        });
        document.addEventListener('click', () => contextMenu.style.display = 'none');
    }

    if (completedCheckbox) completedCheckbox.addEventListener('change', applyFilters);
    if (pendingCheckbox) pendingCheckbox.addEventListener('change', applyFilters);
    if (modeToggle) modeToggle.addEventListener('change', applyFilters);
    if (searchInput) searchInput.addEventListener('input', applyFilters);
    if (searchFieldSelect) searchFieldSelect.addEventListener('change', applyFilters);
    if (refreshBtn) refreshBtn.addEventListener('click', () => window.location.reload());

    applyFilters();
});