document.addEventListener('DOMContentLoaded', function() {

    

    // --- 2. DOM ELEMENTS ---
    const cmfForm = document.querySelector('.cmf-entry-form');
    const saveBtn = document.querySelector('.btn-save');
    const newBtn = document.querySelector('.btn-new');
    const printBtn = document.querySelector('.btn-print'); // Changed selector to class
    const refreshBtn = document.getElementById('refreshBtn');
    
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

    // --- 4. BUTTON LISTENERS (THE FIX IS HERE) ---

    if (saveBtn && cmfForm) {
        saveBtn.addEventListener('click', function() {
            // 1. Validate Form
            if (cmfForm.reportValidity()) {
                // 2. Check if updating or saving new
                // We check the value of the hidden field 'original_cmf_no'
                const hiddenInput = cmfForm.querySelector('input[name="original_cmf_no"]');
                const isUpdate = hiddenInput && hiddenInput.value.trim() !== '';

                // 3. Trigger Confirmation
                Preline.confirm(
                    isUpdate ? 'Update Entry?' : 'Save Entry?',
                    isUpdate
                        ? 'Are you sure you want to update this color matching entry? Existing records will be modified.'
                        : 'Are you sure you want to save this new color matching entry? Please verify all technical specs before confirming.',
                    'success',
                    () => {
                        cmfForm.submit();
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
        printBtn.addEventListener('click', () => {
            window.print();
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
});