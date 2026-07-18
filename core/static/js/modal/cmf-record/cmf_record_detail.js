document.addEventListener('DOMContentLoaded', function () {
    const recordsTbody = document.getElementById('recordsTbody');
    const modalElement = document.getElementById('cmfDetailModal');
    if (!modalElement) return;

    const modalTableBody = modalElement.querySelector('#modalTableBody');
    const bsModal = new bootstrap.Modal(modalElement);

    // 1. ASYNC DOUBLE CLICK TRIGGER
    recordsTbody.addEventListener('dblclick', async function (e) {
        const tr = e.target.closest('.record-row');
        if (!tr) return;

        const cmfNo = tr.cells[0].innerText.trim();
        modalTableBody.innerHTML = '<tr><td colspan="7" class="text-center py-4">Loading history...</td></tr>';
        bsModal.show();

        try {
            const response = await fetch(`/cmf/records/${cmfNo}/`);
            const historyData = await response.json();

            modalTableBody.innerHTML = ''; // Clear loader

            if (historyData.length > 0) {
                // Loop through every formula found in database (MB and DC)
                historyData.forEach(item => {
                    addFormulaSetToModal(item);
                });
            } else {
                modalTableBody.innerHTML = '<tr><td colspan="7" class="text-center py-4 text-muted">No formula history found for this CMF.</td></tr>';
            }
        } catch (error) {
            modalTableBody.innerHTML = '<tr><td colspan="7" class="text-center py-4 text-danger">Error loading data.</td></tr>';
        }
    });

    // 2. RENDER MULTIPLE FORMULA SETS
    function addFormulaSetToModal(data) {
        // Unique ID for toggling: e.g., "formula-MB-10"
        const rowId = `row-${data.formula_no.replace(/[^a-zA-Z0-9]/g, '-')}`;

        const html = `
            <!-- Formula Header Row -->
            <tr class="main-detail-row" style="cursor:pointer;">
                <td class="text-center">
                    <i class="bi bi-plus-circle-fill toggle-icon" style="color: var(--sidebar-header-bg);"></i>
                </td>
                <td class="fw-bold">${data.formula_no}</td>
                <td><span class="badge bg-dark-subtle text-dark border">${data.type}</span></td>
                <td>${data.lot_no}</td>
                <td>${data.matched_by}</td>
                <td>${data.date}</td>
                <td><span class="badge bg-success-subtle text-success border border-success">${data.status}</span></td>
            </tr>
            <!-- Ingredient Sub-row -->
            <tr class="formula-row d-none">
                <td colspan="7" class="p-2 border-0">
                    <div class="formula-container shadow-sm border rounded">
                        <div class="formula-card-header">
                            <span class="extra-small fw-bold"><i class="bi bi-flask me-1"></i> INGREDIENTS BREAKDOWN</span>
                        </div>
                        <table class="table table-sm mb-0">
                            <thead>
                                <tr class="extra-small">
                                    <th class="ps-4 border-0">Material Name</th>
                                    <th class="text-end border-0">Value (%)</th>
                                    <th class="text-end border-0 pe-4">Weight (g)</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${data.ingredients.map(f => `
                                    <tr class="extra-small">
                                        <td class="ps-4 border-0">${f.material}</td>
                                        <td class="text-end border-0 fw-bold" style="color: var(--sidebar-header-bg);">${parseFloat(f.value).toFixed(4)}%</td>
                                        <td class="text-end border-0 pe-4">${parseFloat(f.weight).toFixed(2)}g</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                </td>
            </tr>
        `;
        modalTableBody.insertAdjacentHTML('beforeend', html);
    }

    // 3. TOGGLE LOGIC (Handles multiple rows)
    modalTableBody.addEventListener('click', function (e) {
        const mainRow = e.target.closest('.main-detail-row');
        if (!mainRow) return;

        const formulaRow = mainRow.nextElementSibling;
        const icon = mainRow.querySelector('.toggle-icon');

        if (formulaRow && formulaRow.classList.contains('formula-row')) {
            const isHidden = formulaRow.classList.contains('d-none');
            if (isHidden) {
                formulaRow.classList.remove('d-none');
                icon.className = 'bi bi-dash-circle-fill toggle-icon text-danger';
            } else {
                formulaRow.classList.add('d-none');
                icon.className = 'bi bi-plus-circle-fill toggle-icon';
                icon.style.color = 'var(--sidebar-header-bg)';
            }
        }
    });
});