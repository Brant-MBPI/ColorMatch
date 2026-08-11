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

        // IF we are on the MB page, the MB script handles calculations. 
        // We stop the shared script from overwriting values.
        if (document.querySelector('input[name="record_type"][value="mb"]') || 
            window.location.pathname.includes('formula-mb')) { 
            return; 
        }

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
    const saveBtn = document.querySelector('.btn-save-formula');
    const newBtn = document.querySelector('.btn-new');
    const printBtn = document.querySelector('.btn-print');
    const form = saveBtn ? saveBtn.closest('form') : null;

    if (saveBtn && form) {
        saveBtn.addEventListener('click', function () {
            // 1. Check basic HTML5 validation first
            if (!form.reportValidity()) return;

            // --- MASTERBATCH (MB) SPECIFIC VALIDATION ---
            // We check if the form has the class we added in the template
            const isMB = form.classList.contains('js-mb-formula');
            const isDC = form.classList.contains('js-dc-formula');

            // Get values from the summary row and the supposed weight input
            const totalPct = parseFloat(document.querySelector('.js-total-percent-summary')?.value) || 0;
            const totalWgt = parseFloat(document.querySelector('.js-total-weight-summary')?.value) || 0;
            const masterWgt = parseFloat(document.querySelector('.total-weight-display')?.value) || 0;
            
            if (isMB) {
                // Validation A: Total percentage must be exactly 100
                // Using .toFixed(2) to handle tiny floating point math errors
                if (totalPct.toFixed(2) !== "100.00") {
                    Preline.toast(`Cannot Save: Total percentage must be 100.00%. Currently: ${totalPct.toFixed(4)}%`, 'error');
                    return; // Stop the save
                }

                // Validation B: Summary weight must match the supposed total weight input
                if (totalWgt.toFixed(2) !== masterWgt.toFixed(2)) {
                    Preline.toast(`Cannot Save: Summary weight (${totalWgt.toFixed(2)}) does not match Supposed Total Weight (${masterWgt.toFixed(2)}).`, 'error');
                    return; // Stop the save
                }
            }
            if (isDC) {
                if (totalWgt.toFixed(2) !== masterWgt.toFixed(2)) {
                    Preline.toast(`Cannot Save: Summary weight (${totalWgt.toFixed(2)}) does not match Supposed Total Weight (${masterWgt.toFixed(2)}).`, 'error');
                    return; // Stop the save
                }
            }
            // --------------------------------------------

            // 2. If it's DC or MB validation passed, proceed to confirmation
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


    //  Shared AJAX Auto-population Logic for MB and DC
    const cmfSelectMB = document.getElementById('id_mb_cmf_number');
    const cmfSelectDC = document.getElementById('id_dc_cmf_number');
    const isDC = !!cmfSelectDC;
    const cmfSelectEl = cmfSelectMB || cmfSelectDC;

    async function fetchCmfDetails(cmfNo) {
        // Map IDs based on which page is active
        const fields = {
            customer: isDC ? 'id_dc_customer' : 'id_customer',
            resin: isDC ? 'id_dc_resin' : 'id_resin_used',
            color: isDC ? 'id_dc_color' : 'id_color',
            product: isDC ? 'id_dc_product_code' : 'id_product',
            dosage: isDC ? 'id_dc_dosage' : 'id_dosage',
            application: isDC ? 'id_dc_application' : 'id_application',
            finished_product: isDC ? 'id_dc_finished_product' : 'id_finished_product'
        };

        try {
            const response = await fetch(`/cmf/mb-dc-formula/?cm_no=${encodeURIComponent(cmfNo)}`);
            if (!response.ok) throw new Error('Network response was not ok');
            const data = await response.json();

            const setVal = (id, val) => {
                const el = document.getElementById(id);
                if (el) el.value = val || '';
            };

            setVal(fields.customer, data.customer);
            setVal(fields.resin, data.resin_used || data.resin);
            setVal(fields.color, data.color);
            setVal(fields.application, data.application);
            setVal(fields.finished_product, data.finished_product);
            setVal(fields.product, data.product || data.product_code);
            setVal(fields.dosage, data.dosage);

            Preline.toast(`Details for ${cmfNo} loaded.`, 'success');
            
        } catch (error) {
            console.error('Error fetching CMF details:', error);
            
            Preline.toast('Error fetching details from server.', 'danger');
            
        }
    }

    const initAutoPop = () => {
        if (cmfSelectEl && cmfSelectEl.tagName === 'SELECT') {
            let tsAttempts = 0;
            const pollTomSelect = setInterval(() => {
                tsAttempts++;
                if (cmfSelectEl.tomselect) {
                    clearInterval(pollTomSelect);
                    
                    cmfSelectEl.tomselect.on('change', function(value) {
                        if (!value) return;

                       
                        Preline.confirm(
                            'Load Record Details?',
                            `Do you want to automatically fill the form with details from CMF #${value}?`,
                            'info',
                            () => fetchCmfDetails(value), 
                            () => { console.log("User cancelled auto-fill."); }
                        );
                    });
                } else if (tsAttempts > 50) {
                    clearInterval(pollTomSelect);
                }
            }, 100);
        }
    };

    initAutoPop();

})();