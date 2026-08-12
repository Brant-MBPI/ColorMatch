document.addEventListener('DOMContentLoaded', function() {

    // --- 2. DOM ELEMENTS ---
    const cmfInput = document.getElementById('id_cmf_no');
    const saveBtn = document.querySelector('.btn-save');
    const newBtn = document.querySelector('.btn-new');
    const printBtn = document.querySelector('.btn-cmf-print');
    const refreshBtn = document.getElementById('refreshBtn');

    // Works on any page — CMF Entry, RS Entry, or anywhere else these
    // buttons appear — since it finds whichever <form> actually wraps
    // the Save button, instead of relying on a hardcoded form class.
    const entryForm = saveBtn ? saveBtn.closest('form') : null;

    const completedCheckbox = document.getElementById('completed');
    const pendingCheckbox = document.getElementById('pending');
    const modeToggle = document.getElementById('modeToggle');
    const searchInput = document.getElementById('recordSearchInput');
    const searchFieldSelect = document.getElementById('searchFieldSelect');
    const recordsTbody = document.getElementById('recordsTbody');

    // --- 3. NUMERIC INPUT FORMATTING LOGIC ---
    const restrictToNumbers = (e) => {
        const charCode = (e.which) ? e.which : e.keyCode;
        if (charCode !== 46 && charCode > 31 && (charCode < 48 || charCode > 57)) { e.preventDefault(); return false; }
        if (charCode === 46 && e.target.value.indexOf('.') !== -1) { e.preventDefault(); return false; }
        return true;
    };

    document.querySelectorAll('.qty-resin-input, .dosage-input').forEach(input => {
        input.addEventListener('keypress', restrictToNumbers);
    });

    // --- 4. BUTTON LISTENERS ---

    if (saveBtn && entryForm) {
        saveBtn.addEventListener('click', function() {
            // 1. Validate Form
            if (entryForm.reportValidity()) {
                // 2. Check if updating or saving new.
                // CMF Entry uses original_cmf_no, RS Entry uses original_rs_no,
                // Pending/Completed uses record_no (it's update-only, no "new" state).
                const hiddenInput = entryForm.querySelector(
                    '[name="original_cmf_no"], [name="original_rs_no"], [name="record_no"]'
                );
                const isUpdate = hiddenInput && hiddenInput.value.trim() !== '';

                // 3. Trigger Confirmation
                Preline.confirm(
                    isUpdate ? 'Update Entry?' : 'Save Entry?',
                    isUpdate
                        ? 'Are you sure you want to update this entry? Existing records will be modified.'
                        : 'Are you sure you want to save this new entry? Please verify all technical specs before confirming.',
                    'success',
                    () => {
                        entryForm.submit();
                    }
                );
            }
        });
    }

    if (newBtn) {
        newBtn.addEventListener('click', function() {
            Preline.confirm(
                'Create New?', 
                'Any unsaved changes on this form will be lost. Do you want to continue?', 
                'warning', 
                () => {
                    // Redirect to clear the form (clears ?no= query string)
                    window.location.href = window.location.pathname; 
                }
            );
        });
    }

    if (printBtn) {
            printBtn.addEventListener('click', function() {
                const cmNo = cmfInput.value.trim();

                // 1. Client-side validation (Immediate UI feedback)
                if (!cmNo) {
                    Preline.confirm(
                        'Missing CMF',
                        'Please enter or load a Color Matching No. before printing.',
                        'danger',
                        () => { /* No action, just closes */ }
                    );
                    return;
                }

                // 2. Proceed to print (New Tab)
                const printUrl = `/cmf/print/${encodeURIComponent(cmNo)}`;
                window.location.href = printUrl; 
                // Note: Using window.location.href instead of window.open ensures 
                // that if a redirect (error) happens, it stays in the same tab.
            });
        }

    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => window.location.reload());
    }

    // --- 5. REUSABLE "OTHERS" TOGGLE LOGIC ---
    const updateOtherInputState = (trigger, input) => {
        if (trigger.checked) {
            input.disabled = false;
            input.required = true;
        } else {
            input.disabled = true;
            input.required = false;
            input.value = ""; 
        }
    };

    document.querySelectorAll('.js-other-container').forEach(container => {
        const trigger = container.querySelector('.js-other-trigger');
        const input = container.querySelector('.js-other-input');
        if (!trigger || !input) return;

        if (trigger.type === 'checkbox') {
            trigger.addEventListener('change', () => updateOtherInputState(trigger, input));
        } else if (trigger.type === 'radio') {
            const groupName = trigger.name;
            document.querySelectorAll(`input[name="${groupName}"]`).forEach(radio => {
                radio.addEventListener('change', () => updateOtherInputState(trigger, input));
            });
        }
        updateOtherInputState(trigger, input);
    });

    // --- 6. TABLE FILTERING LOGIC (Records View) ---
    function applyFilters() {
        if (!recordsTbody) return; // Only run if on the records page
        
        const isRsMode = modeToggle ? modeToggle.checked : false;
        const currentMode = isRsMode ? 'rs' : 'cmf';
        const showCompleted = completedCheckbox?.checked ?? true;
        const showPending = pendingCheckbox?.checked ?? true;
        const searchTerm = searchInput?.value.trim().toLowerCase() ?? '';

        document.querySelectorAll('.record-row').forEach(row => {
            const matchesMode = row.dataset.mode === currentMode;
            const rowStatus = row.dataset.status;
            const matchesStatus = (showCompleted && rowStatus === 'Completed') || (showPending && rowStatus === 'Pending');
            const matchesSearch = searchTerm === '' || row.textContent.toLowerCase().includes(searchTerm);

            row.style.display = (matchesMode && matchesStatus && matchesSearch) ? '' : 'none';
        });
    }

    [completedCheckbox, pendingCheckbox, modeToggle].forEach(el => el?.addEventListener('change', applyFilters));
    searchInput?.addEventListener('input', applyFilters);

    // Initial run
    applyFilters();

    // The function that checks the database
    const handleCmfLookup = debounce(async (event) => {
        const query = event.target.value;
        if (query.length < 3) return; // Don't search for very short strings

        try {
            const response = await fetch(`/check-previous-matching/?cm_no=${query}`);
            const data = await response.json();

            if (data.match) {
                Preline.confirm(
                    'Previous Matching Found',
                    `A previous record (${data.latest_cm_no}) exists. Do you want to auto-fill the fields with its data?`,
                    'info',
                    () => {
                        // CONFIRMED: Redirect to load data but keep the user's NEW ID
                        const userInput = cmfInput.value;
                        window.location.href = `/cmf/entry/?no=${data.latest_cm_no}&new_no=${userInput}`;
                    },
                    () => {
                        // CANCELLED: Do nothing, let the user continue typing manually
                    }
                );
            }
        } catch (error) {
            console.error("Error fetching matching data:", error);
        }
    }, 800);

    // Attach to the input event
    if (cmfInput) {
        cmfInput.addEventListener('input', handleCmfLookup);
    }
});