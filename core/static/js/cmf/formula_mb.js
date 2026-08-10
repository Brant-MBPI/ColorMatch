/**
 * Shared Formula Logic for MB and DC
 * Handles:
 * 1. Automatic weight/percentage calculations
 * 2. AJAX Auto-population of form details with Preline Confirmation
 */
(function () {
    // --- 1. SELECTION & DETECTION ---
    const table = document.querySelector('.js-formula-table');
    const supposedWeightInput = document.querySelector('.total-weight-display');
    const summaryTotalPercent = document.querySelector('.js-total-percent-summary');
    const summaryTotalWeight = document.querySelector('.js-total-weight-summary');

    // Detect Page Type based on IDs present in the HTML
    const cmfSelectMB = document.getElementById('id_mb_cmf_number');
    const cmfSelectDC = document.getElementById('id_dc_cmf_number');
    const isDC = !!cmfSelectDC;
    const cmfSelectEl = cmfSelectMB || cmfSelectDC;

    // --- 2. CALCULATION LOGIC ---

    function calculateRowWeight(row) {
        if (!supposedWeightInput) return;
        const percentInput = row.querySelector('.js-percent-input');
        const weightInput = row.querySelector('.js-weight-input');
        const masterWeight = parseFloat(supposedWeightInput.value) || 0;
        const percent = parseFloat(percentInput.value) || 0;

        if (masterWeight > 0 && percent >= 0) {
            const calculatedWeight = masterWeight * (percent / 100);
            weightInput.value = calculatedWeight.toFixed(4);
        } else if (percent === 0) {
            weightInput.value = "";
        }
    }

    function updateSummaryTotals() {
        if (!table) return;
        let totalPct = 0;
        let totalWgt = 0;

        table.querySelectorAll('.js-percent-input').forEach(input => {
            totalPct += parseFloat(input.value) || 0;
        });

        table.querySelectorAll('.js-weight-input').forEach(input => {
            totalWgt += parseFloat(input.value) || 0;
        });

        if (summaryTotalPercent) {
            summaryTotalPercent.value = totalPct.toFixed(4);
            summaryTotalPercent.style.color = (totalPct.toFixed(2) !== "100.00") ? "#dc3545" : "#198754";
        }

        if (summaryTotalWeight && supposedWeightInput) {
            summaryTotalWeight.value = totalWgt.toFixed(4);
            const masterWgt = parseFloat(supposedWeightInput.value) || 0;
            summaryTotalWeight.style.color = (totalWgt.toFixed(2) !== masterWgt.toFixed(2)) ? "#dc3545" : "#198754";
        }
    }

    // --- 3. AUTO-POPULATION LOGIC (AJAX) ---

    async function fetchCmfDetails(cmfNo) {
        // ID Mapping based on page detection
        const fields = {
            customer: isDC ? 'id_dc_customer' : 'id_customer',
            resin: isDC ? 'id_dc_resin' : 'id_resin_used',
            color: isDC ? 'id_dc_color' : 'id_color',
            product: isDC ? 'id_dc_product_code' : 'id_product',
            dosage: isDC ? 'id_dc_dosage' : 'id_dosage',
            application: isDC ? 'id_dc_application' : 'id_application',
            finished_product: isDC ? 'id_dc_finished_product' : 'id_finished_product'
        };

        // Show loading state
        Object.values(fields).forEach(id => {
            const el = document.getElementById(id);
            if (el) el.placeholder = "Loading...";
        });

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

            if (window.Preline && Preline.toast) {
                Preline.toast(`Details for ${cmfNo} loaded.`, 'success');
            }
        } catch (error) {
            console.error('Error fetching CMF details:', error);
            if (window.Preline && Preline.toast) {
                Preline.toast('Error fetching details from server.', 'danger');
            }
        } finally {
            Object.values(fields).forEach(id => {
                const el = document.getElementById(id);
                if (el) el.placeholder = "";
            });
        }
    }

    // --- 4. INITIALIZATION & EVENT LISTENERS ---

    const init = () => {
        // Table Input Listeners (for Weight/Percent updates)
        if (table) {
            table.addEventListener('input', function(e) {
                if (e.target.classList.contains('js-percent-input')) {
                    calculateRowWeight(e.target.closest('tr'));
                    updateSummaryTotals();
                }
                if (e.target.classList.contains('js-weight-input')) {
                    updateSummaryTotals();
                }
            });
        }

        // Total Weight Input Listener
        if (supposedWeightInput) {
            supposedWeightInput.addEventListener('input', function() {
                if (table) {
                    table.querySelectorAll('tbody tr').forEach(row => calculateRowWeight(row));
                }
                updateSummaryTotals();
            });
        }

        // CMF Selector Listener (AJAX + Confirmation)
        if (cmfSelectEl && cmfSelectEl.tagName === 'SELECT') {
            // Polling to wait for TomSelect to attach to the element
            let tsAttempts = 0;
            const pollTomSelect = setInterval(() => {
                tsAttempts++;
                if (cmfSelectEl.tomselect) {
                    clearInterval(pollTomSelect);
                    
                    cmfSelectEl.tomselect.on('change', function(value) {
                        if (!value) return;

                        // PRELINE CONFIRMATION
                        if (window.Preline && typeof Preline.confirm === 'function') {
                            Preline.confirm(
                                'Load Record Details?',
                                `Do you want to automatically fill the form with details from CMF #${value}?`,
                                'info',
                                () => fetchCmfDetails(value), // Confirmed: Run AJAX
                                () => { /* Cancelled: Do nothing */ }
                            );
                        } else {
                            // Fallback if Preline is not detected
                            if (confirm(`Load details for ${value}?`)) fetchCmfDetails(value);
                        }
                    });
                } else if (tsAttempts > 50) {
                    clearInterval(pollTomSelect);
                    console.warn("TomSelect failed to initialize on CMF Selector.");
                }
            }, 100);
        }

        updateSummaryTotals();
    };

    // Execution
    init();

})();