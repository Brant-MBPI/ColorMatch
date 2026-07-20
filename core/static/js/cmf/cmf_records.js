document.addEventListener('DOMContentLoaded', function() {

    // --- TOM SELECT INITIALIZATION ---
    document.querySelectorAll('.ts-select').forEach((el) => {
        new TomSelect(el, {
            plugins: ['remove_button'],
            create: false,
            persist: false,
            placeholder: el.getAttribute('placeholder') || "Select options...",
            maxOptions: null,
            onItemAdd: function() {
                this.setTextboxValue('');
                this.refreshOptions();
            }
        });
    });

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

    // Context Menu Elements
    const contextMenu = document.getElementById('customContextMenu');
    const menuTitle = document.getElementById('contextMenuTitle');
    const linkCmfEntry = document.getElementById('linkCmfEntry');
    const linkMbFormula = document.getElementById('linkMbFormula');
    const linkDcFormula = document.getElementById('linkDcFormula');
    const recordsTbody = document.getElementById('recordsTbody');

    // Column Indexes matching services.py
    const COLS_BOTH = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9];
    const COLS_COMPLETED = [0, 1, 2, 3, 4, 7, 8, 10, 11];
    const COLS_PENDING = [0, 1, 2, 3, 4, 5, 6, 7, 12];

    function applyFilters() {
        const isRsMode = modeToggle ? modeToggle.checked : false;
        const currentMode = isRsMode ? 'rs' : 'cmf';
        const showCompleted = completedCheckbox ? completedCheckbox.checked : true;
        const showPending = pendingCheckbox ? pendingCheckbox.checked : true;
        const searchTerm = searchInput ? searchInput.value.trim().toLowerCase() : '';
        const searchColIndex = searchFieldSelect ? searchFieldSelect.value : 'all';

        // 1. UPDATE MODE LABELS
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

        // 2. DETERMINE ACTIVE COLUMNS
        let activeCols = [];
        if (showCompleted && showPending) {
            activeCols = COLS_BOTH;
        } else if (showCompleted) {
            activeCols = COLS_COMPLETED;
        } else if (showPending) {
            activeCols = COLS_PENDING;
        }

        // 3. TOGGLE COLUMN HEADERS & CELLS VISIBILITY
        for (let i = 0; i <= 12; i++) {
            const isVisible = activeCols.includes(i);
            const cells = document.querySelectorAll(`[data-col-index="${i}"]`);
            cells.forEach(cell => {
                cell.style.display = isVisible ? '' : 'none';
            });
        }

        // 4. FILTER ROWS
        let visibleCount = 0;
        const rows = document.querySelectorAll('.record-row');

        rows.forEach(row => {
            const rowMode = row.dataset.mode;
            const rowStatus = row.dataset.status;

            // Check Mode Match
            const matchesMode = (rowMode === currentMode);

            // Check Status Match
            let matchesStatus = false;
            if (showCompleted && rowStatus === 'Completed') matchesStatus = true;
            if (showPending && rowStatus === 'Pending') matchesStatus = true;

            // Check Search Term Match
            let matchesSearch = true;
            if (searchTerm !== '') {
                if (searchColIndex === 'all') {
                    matchesSearch = row.textContent.toLowerCase().includes(searchTerm);
                } else {
                    const targetCell = row.querySelector(`[data-col-index="${searchColIndex}"]`);
                    matchesSearch = targetCell ? targetCell.textContent.toLowerCase().includes(searchTerm) : false;
                }
            }

            // Apply Display
            if (matchesMode && matchesStatus && matchesSearch) {
                row.style.display = '';
                visibleCount++;
            } else {
                row.style.display = 'none';
            }
        });

        // 5. UPDATE COUNTER
        if (recordCounter) {
            recordCounter.textContent = `Showing ${visibleCount} records`;
        }
    }

    // --- RIGHT CLICK (CONTEXT MENU) LOGIC ---
    if (recordsTbody && contextMenu) {
        recordsTbody.addEventListener('contextmenu', function (e) {
            const tr = e.target.closest('.record-row');
            if (!tr) return;

            // Stop native browser menu
            e.preventDefault();

            const cmfNo = tr.cells[0].innerText.trim();
            const rowMode = tr.dataset.mode; // 'cmf' or 'rs'

            // Update UI
            menuTitle.innerText = cmfNo;

            // Update Links based on CMF Number
            // Ensure these match your Django URLs
            linkCmfEntry.href = `/cmf/entry/?no=${encodeURIComponent(cmfNo)}`;
            linkMbFormula.href = `/cmf/mb-formula/?no=${encodeURIComponent(cmfNo)}`;
            linkDcFormula.href = `/cmf/dc-formula/?no=${encodeURIComponent(cmfNo)}`;

            // Positioning
            const x = e.clientX;
            const y = e.clientY;

            // Adjust position if menu goes off screen
            const menuWidth = 200; 
            const menuHeight = 150;
            const windowWidth = window.innerWidth;
            const windowHeight = window.innerHeight;

            const posX = (x + menuWidth > windowWidth) ? x - menuWidth : x;
            const posY = (y + menuHeight > windowHeight) ? y - menuHeight : y;

            contextMenu.style.top = `${posY}px`;
            contextMenu.style.left = `${posX}px`;
            contextMenu.style.display = 'block';
        });

        // Hide menu on any left click outside
        document.addEventListener('click', function (e) {
            if (!contextMenu.contains(e.target)) {
                contextMenu.style.display = 'none';
            }
        });

        // Hide menu on scroll
        window.addEventListener('scroll', function () {
            contextMenu.style.display = 'none';
        }, true);
    }

    // --- EVENT LISTENERS ---
    if (completedCheckbox) completedCheckbox.addEventListener('change', applyFilters);
    if (pendingCheckbox) pendingCheckbox.addEventListener('change', applyFilters);
    if (modeToggle) modeToggle.addEventListener('change', applyFilters);
    if (searchInput) searchInput.addEventListener('input', applyFilters);
    if (searchFieldSelect) searchFieldSelect.addEventListener('change', applyFilters);

    if (refreshBtn) {
        refreshBtn.addEventListener('click', function() {
            window.location.reload();
        });
    }

    // INITIAL FILTER RUN
    applyFilters();
});