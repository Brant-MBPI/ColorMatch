(function () {
    // --- 1. TOM SELECT INITIALIZATION ---
    document.querySelectorAll('.ts-select-table').forEach((el) => {
        if (el.tomselect) return; // Prevent double init
        
        new TomSelect(el, {
            selectOnTab: true,
            create: false,
            placeholder: "Search material...",
            maxOptions: 50,
            dropdownParent: 'body',
            onItemAdd: function () {
                this.blur();
            },
            onInitialize: function() {
                // Trigger validation logic on load for existing data
                updateRowRequirement(this.input);
            },
            onChange: function() {
                // Trigger validation and calculation when material changes
                updateRowRequirement(this.input);
                calculateFormulaTotals(this.input.closest('.js-formula-table'));
            }
        });
    });

    // --- 2. Dynamic Row Validation (If Col 1 has data, Col 2 is required) ---
    function updateRowRequirement(selectEl) {
        const row = selectEl.closest('tr');
        if (!row) return;
        const percentInput = row.querySelector('.js-percent-input');
        if (!percentInput) return;

        if (selectEl.value && selectEl.value.trim() !== "") {
            percentInput.required = true;
            percentInput.classList.add('bg-warning-subtle'); // Subtle visual hint
        } else {
            percentInput.required = false;
            percentInput.classList.remove('bg-warning-subtle');
        }
    }

    // --- 3. Formula Auto-Calculation (Replaces old Weight-only Logic) ---
    function calculateFormulaTotals(table) {
        if (!table) return;

        let totalPercent = 0;
        let totalWeight = 0;

        const percentInputs = table.querySelectorAll('.js-percent-input');
        const weightInputs = table.querySelectorAll('.js-weight-input');
        const totalPercentDisplay = table.querySelector('.js-total-percent-summary');
        const totalWeightDisplay = table.querySelector('.js-total-weight-summary');
        const externalWeightDisplay = document.querySelector('.total-weight-display');

        percentInputs.forEach(input => {
            totalPercent += parseFloat(input.value) || 0;
        });

        weightInputs.forEach(input => {
            totalWeight += parseFloat(input.value) || 0;
        });

        // Update Summary Footer Labels
        if (totalPercentDisplay) {
            totalPercentDisplay.value = totalPercent.toFixed(4);
            totalPercentDisplay.style.color = totalPercent > 100.0001 ? 'red' : '';
        }

        if (totalWeightDisplay) {
            totalWeightDisplay.value = totalWeight.toFixed(4);
        }

        // Sync with your original external "Total Weight" input
        if (externalWeightDisplay) {
            externalWeightDisplay.value = totalWeight.toFixed(4);
        }
    }

    // Listen for all typing inside formula tables
    document.addEventListener('input', function (e) {
        const table = e.target.closest('.js-formula-table');
        if (table && (e.target.classList.contains('js-percent-input') || e.target.classList.contains('js-weight-input'))) {
            calculateFormulaTotals(table);
        }
    });

    // --- 4. Reusable Hex Preview & Validation ---
    const hexInput = document.querySelector('.hex-input');
    const swatch = document.querySelector('.color-swatch');

    if (hexInput && swatch) {
        const isValidHex = (value) => /^#([0-9A-Fa-f]{3}){1,2}$/.test(value);

        hexInput.addEventListener('input', function () {
            let value = hexInput.value.trim();
            if (value && !value.startsWith('#')) value = '#' + value;
            if (isValidHex(value)) swatch.style.backgroundColor = value;
        });

        hexInput.addEventListener('blur', function () {
            let value = hexInput.value.trim();
            if (value === "") { swatch.style.backgroundColor = "#FFFFFF"; return; }
            if (!value.startsWith('#')) value = '#' + value;

            if (!isValidHex(value)) {
                hexInput.value = "";
                swatch.style.backgroundColor = "#FFFFFF";
            } else {
                hexInput.value = value;
            }
        });
    }

    // --- 5. Save / New / Print button confirmations ---
    const saveBtn = document.querySelector('.btn-save');
    const newBtn = document.querySelector('.btn-new');
    const printBtn = document.querySelector('.btn-print');
    const form = saveBtn ? saveBtn.closest('form') : null;

    if (saveBtn && form) {
        saveBtn.addEventListener('click', function () {
            if (form.reportValidity()) {
                const formulaIdInput = form.querySelector('[name="formula_id"]');
                const isUpdate = formulaIdInput && formulaIdInput.value.trim() !== '';

                Preline.confirm(
                    isUpdate ? 'Update Formula?' : 'Save Formula?',
                    isUpdate
                        ? 'Are you sure you want to update this formula? Please verify all technical specs before confirming.'
                        : 'Are you sure you want to save this formula? Please verify all technical specs before confirming.',
                    'success',
                    () => {
                        form.submit();
                    }
                );
            }
        });
    }

    if (newBtn) {
        newBtn.addEventListener('click', function () {
            Preline.confirm(
                'Create New?',
                'Any unsaved changes on this form will be lost. Do you want to continue?',
                'warning',
                () => {
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

    // Run calculation once on load to populate totals if data exists
    const initialTable = document.querySelector('.js-formula-table');
    if(initialTable) calculateFormulaTotals(initialTable);

})();