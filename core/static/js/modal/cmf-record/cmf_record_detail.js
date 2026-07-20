document.addEventListener('DOMContentLoaded', function () {
    const recordsTbody = document.getElementById('recordsTbody');
    const modalElement = document.getElementById('cmfDetailModal');
    if (!modalElement) return;

    const modalTableBody = modalElement.querySelector('#modalTableBody');
    const bsModal = new bootstrap.Modal(modalElement);

    recordsTbody.addEventListener('dblclick', async function (e) {
        const tr = e.target.closest('.record-row');
        if (!tr) return;

        const cmfNo = tr.cells[0].innerText.trim();
        modalTableBody.innerHTML = '<tr><td colspan="7" class="text-center py-4">Fetching CMF Details...</td></tr>';
        bsModal.show();

        try {
            const response = await fetch(`/cmf/records/${encodeURIComponent(cmfNo)}/`);
            const dataList = await response.json(); // This is a list of CMF objects

            modalTableBody.innerHTML = ''; 

            if (dataList.length > 0) {
                dataList.forEach(cmf => {
                    addCmfRowToModal(cmf);
                });
            } else {
                modalTableBody.innerHTML = '<tr><td colspan="7" class="text-center py-4 text-muted">No records found.</td></tr>';
            }
        } catch (error) {
            console.log('Error fetching CMF details:', error);
            modalTableBody.innerHTML = '<tr><td colspan="7" class="text-center py-4 text-danger">Error fetching database records.</td></tr>';
        }
    });

    function addCmfRowToModal(cmf) {
        let mbTableHtml = '';
        let dcTableHtml = '';

        // Check MB Formulas
        if (cmf.mb_formulas && cmf.mb_formulas.length > 0) {
            mbTableHtml = `
                <div class="mb-4">
                    <div class="p-2 mb-2 border-bottom border-teal d-flex align-items-center">
                        <i class="bi bi-gear-fill text-teal me-2"></i>
                        <h6 class="extra-small fw-bold mb-0 text-teal uppercase">MB Extruder Formulas</h6>
                    </div>
                    <table class="table table-sm border small mb-0">
                        <thead class="bg-light extra-small">
                            <tr>
                                <th>Date</th><th>Product Code</th><th>Lot Number</th><th>Color</th><th>Mixing Time</th><th>Matched By</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${cmf.mb_formulas.map(f => `
                                <tr class="fw-bold bg-light-subtle">
                                    <td>${f.date}</td><td>${f.prod_code}</td><td>${f.lot_no}</td><td>${f.color}</td><td>${f.mixing_time}</td><td>${f.matched_by}</td>
                                </tr>
                                <tr>
                                    <td colspan="6" class="p-0 border-0">
                                        <table class="table table-sm mb-0 table-borderless">
                                            <tbody class="text-muted small">
                                                ${f.ingredients.map(ing => `
                                                    <tr>
                                                        <td style="width: 40%;" class="ps-5">${ing.material}</td>
                                                        <td style="width: 30%;" class="text-end">${ing.value.toFixed(4)}%</td>
                                                        <td style="width: 30%;" class="text-end pe-5">${ing.weight.toFixed(2)}g</td>
                                                    </tr>
                                                `).join('')}
                                            </tbody>
                                        </table>
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>`;
        }

        // Check DC Formulas
        if (cmf.dc_formulas && cmf.dc_formulas.length > 0) {
            dcTableHtml = `
                <div class="mb-4">
                    <div class="p-2 mb-2 border-bottom border-teal d-flex align-items-center">
                        <i class="bi bi-box-seam-fill text-teal me-2"></i>
                        <h6 class="extra-small fw-bold mb-0 text-teal uppercase">DC Extruder Formulas</h6>
                    </div>
                    <table class="table table-sm border small mb-0">
                        <thead class="bg-light extra-small">
                            <tr>
                                <th>Date</th><th>Product Code</th><th>Color</th><th>Sample Size</th><th>Mixing Time</th><th>Matched By</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${cmf.dc_formulas.map(f => `
                                <tr class="fw-bold bg-light-subtle">
                                    <td>${f.date}</td><td>${f.prod_code}</td><td>${f.color}</td><td>${f.sample_size}</td><td>${f.mixing_time}</td><td>${f.matched_by}</td>
                                </tr>
                                <tr>
                                    <td colspan="6" class="p-0 border-0">
                                        <table class="table table-sm mb-0 table-borderless">
                                            <tbody class="text-muted small">
                                                ${f.ingredients.map(ing => `
                                                    <tr>
                                                        <td style="width: 40%;" class="ps-5">${ing.material}</td>
                                                        <td style="width: 30%;" class="text-end">${ing.value.toFixed(4)}%</td>
                                                        <td style="width: 30%;" class="text-end pe-5">${ing.weight.toFixed(2)}g</td>
                                                    </tr>
                                                `).join('')}
                                            </tbody>
                                        </table>
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>`;
        }

        // Check if both are empty
        let contentHtml = mbTableHtml + dcTableHtml;
        if (!contentHtml) {
            contentHtml = '<div class="text-center py-5 text-muted fw-bold">No Formula Records Found</div>';
        }

        const html = `
            <tr class="main-detail-row" style="cursor:pointer;">
                <td class="text-center">
                    <i class="bi bi-plus-circle-fill toggle-icon" style="color: var(--sidebar-header-bg);"></i>
                </td>
                <td class="fw-bold">${cmf.cm_no}</td>
                <td>${cmf.customer}</td>
                <td>${cmf.color}</td>
                <td>${cmf.type}</td>
                <td><code>${cmf.code}</code></td>
                <td><span class="badge bg-success-subtle text-success border border-success">${cmf.status}</span></td>
            </tr>
            <tr class="formula-row d-none">
                <td colspan="7" class="p-4 border-0">
                    <div class="formula-container shadow-sm border rounded p-3">
                        ${contentHtml}
                    </div>
                </td>
            </tr>
        `;
        modalTableBody.insertAdjacentHTML('beforeend', html);
    }

    // TOGGLE LOGIC
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