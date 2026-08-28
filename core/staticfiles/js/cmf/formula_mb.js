/**
 * formula_mb.js
 * Logic specific to Masterbatch (MB) Formula.
 * Calculation: [Supposed Total Weight] * ([Row %] / 100) = [Row Weight]
 */
(function () {
    const table = document.querySelector('.js-formula-table');
    const supposedWeightInput = document.querySelector('.total-weight-display');
    const summaryTotalPercent = document.querySelector('.js-total-percent-summary');
    const summaryTotalWeight = document.querySelector('.js-total-weight-summary');

    if (!table || !supposedWeightInput) return;

    /**
     * Calculates a single row's weight based on the supposed total weight and the row's percent
     */
    function calculateRowWeight(row) {
        const percentInput = row.querySelector('.js-percent-input');
        const weightInput = row.querySelector('.js-weight-input');
        const masterWeight = parseFloat(supposedWeightInput.value) || 0;
        const percent = parseFloat(percentInput.value) || 0;

        if (masterWeight > 0 && percent >= 0) {
            const calculatedWeight = masterWeight * (percent / 100);
            weightInput.value = calculatedWeight.toFixed(6);
        } else if (percent === 0) {
            weightInput.value = "";
        }
    }

    /**
     * Sums up all percentages and weights to update the footer summary
     */
    function updateSummaryTotals() {
        let totalPct = 0;
        let totalWgt = 0;

        table.querySelectorAll('.js-percent-input').forEach(input => {
            totalPct += parseFloat(input.value) || 0;
        });

        table.querySelectorAll('.js-weight-input').forEach(input => {
            totalWgt += parseFloat(input.value) || 0;
        });

        // Update Footer UI
        if (summaryTotalPercent) {
            summaryTotalPercent.value = totalPct.toFixed(6);
            // Visual Validation: Red if not 100%
            summaryTotalPercent.style.color = (totalPct.toFixed(2) !== "100.00") ? "#dc3545" : "#198754";
        }

        if (summaryTotalWeight) {
            summaryTotalWeight.value = totalWgt.toFixed(6);
            // Visual Validation: Red if doesn't match supposed weight
            const masterWgt = parseFloat(supposedWeightInput.value) || 0;
            summaryTotalWeight.style.color = (totalWgt.toFixed(2) !== masterWgt.toFixed(2)) ? "#dc3545" : "#198754";
        }
    }

    // EVENT 1: User changes the Supposed Total Weight
    supposedWeightInput.addEventListener('input', function() {
        // When the master weight changes, we must re-calculate EVERY row's weight
        table.querySelectorAll('tbody tr').forEach(row => {
            calculateRowWeight(row);
        });
        updateSummaryTotals();
    });

    // EVENT 2: User changes a Percentage in a row
    table.addEventListener('input', function(e) {
        if (e.target.classList.contains('js-percent-input')) {
            const row = e.target.closest('tr');
            calculateRowWeight(row);
            updateSummaryTotals();
        }

        // EVENT 3: If they manually edit weight (optional, but good for summary)
        if (e.target.classList.contains('js-weight-input')) {
            updateSummaryTotals();
        }
    });

    // Run once on page load (in case of existing data)
    updateSummaryTotals();

})();