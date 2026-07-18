document.addEventListener('DOMContentLoaded', function () {
    const recordsTbody = document.getElementById('recordsTbody');
    const modalElement = document.getElementById('cmfDetailModal');
    
    if (!modalElement) return;
    const modalTableBody = modalElement.querySelector('#modalTableBody');
    const bsModal = new bootstrap.Modal(modalElement);

    // 1. DOUBLE CLICK TRIGGER (Main Records Table)
    recordsTbody.addEventListener('dblclick', function (e) {
        const tr = e.target.closest('.record-row');
        if (!tr) return;

        modalTableBody.innerHTML = ''; // Fresh modal content

        const data = {
            no: tr.cells[0].innerText.trim(),
            customer: tr.cells[1].innerText.trim(),
            color: tr.cells[2].innerText.trim(),
            type: tr.cells[7].innerText.trim(),
            code: tr.cells[8].innerText.trim(),
            status: tr.cells[9].innerHTML.trim(), 
            formulas: [
                { mat: "Titanium Dioxide", pct: "12.50", qty: "125.0", lot: "LOT-A1" },
                { mat: "Organic Red", pct: "87.50", qty: "875.0", lot: "LOT-B2" }
            ]
        };

        addRecordToModal(data);
        bsModal.show();
    });

    // 2. APPEND ROWS
    function addRecordToModal(data) {
        const html = `
            <!-- Parent Row -->
            <tr class="main-detail-row" style="cursor:pointer;">
                <td class="text-center">
                    <i class="bi bi-plus-circle-fill toggle-icon" style="color: var(--sidebar-header-bg);"></i>
                </td>
                <td class="fw-bold">${data.no}</td>
                <td>${data.customer}</td>
                <td>${data.color}</td>
                <td>${data.type}</td>
                <td><code>${data.code}</code></td>
                <td>${data.status}</td>
            </tr>
            <!-- Sub Row (Formula) - Always follows parent -->
            <tr class="formula-row d-none">
                <td colspan="7" class="p-0 border-0">
                    <div class="formula-container shadow-sm border rounded">
                        <div class="formula-card-header p-2 d-flex justify-content-between align-items-center">
                            <span class="extra-small fw-bold"><i class="bi bi-flask me-1"></i> FORMULA DETAILS</span>
                        </div>
                        <table class="table table-sm mb-0">
                            <thead>
                                <tr class="extra-small">
                                    <th class="ps-4 border-0">Material Name</th>
                                    <th class="text-end border-0">Percentage (%)</th>
                                    <th class="text-end border-0">Quantity (g)</th>
                                    <th class="text-center border-0 pe-4">Batch Lot</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${data.formulas.map(f => `
                                    <tr class="extra-small">
                                        <td class="ps-4 border-0">${f.mat}</td>
                                        <td class="text-end border-0 fw-bold" style="color: var(--sidebar-header-bg);">${f.pct}%</td>
                                        <td class="text-end border-0">${f.qty}g</td>
                                        <td class="text-center border-0 pe-4">
                                            <span class="badge bg-secondary-subtle text-dark border">${f.lot}</span>
                                        </td>
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

    // 3. TOGGLE LOGIC (Robust Sibling-based approach)
    modalTableBody.addEventListener('click', function (e) {
        // Find the parent row that was clicked
        const mainRow = e.target.closest('.main-detail-row');
        if (!mainRow) return;

        // The formula row is ALWAYS the next sibling in the DOM
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