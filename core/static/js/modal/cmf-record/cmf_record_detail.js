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
        const html = `
            <!-- CMF PARENT ROW -->
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
            
            <!-- SUB-ROW CONTAINING ALL FORMULAS -->
            <tr class="formula-row d-none">
                <td colspan="7" class="p-3 border-0">
                    <div class="formula-container shadow-sm border rounded p-3">
                        <h6 class="extra-small fw-bold text-teal mb-3">
                            <i class="bi bi-layers-fill me-1"></i> ASSOCIATED FORMULAS FOR ${cmf.cm_no}
                        </h6>
                        
                        ${cmf.formulas.length > 0 ? cmf.formulas.map(form => `
                            <div class="mb-4 border rounded overflow-hidden">
                                <div class="formula-card-header d-flex justify-content-between align-items-center">
                                    <span class="small fw-bold text-uppercase">${form.id} (${form.type})</span>
                                    <span class="extra-small text-muted">Matched by: ${form.matched_by} | ${form.date}</span>
                                </div>
                                <table class="table table-sm mb-0">
                                    <thead class="bg-light extra-small">
                                        <tr>
                                            <th class="ps-3">Material</th>
                                            <th class="text-end">Value (%)</th>
                                            <th class="text-end pe-3">Weight (g)</th>
                                        </tr>
                                    </thead>
                                    <tbody class="extra-small">
                                        ${form.ingredients.map(ing => `
                                            <tr>
                                                <td class="ps-3">${ing.material}</td>
                                                <td class="text-end fw-bold text-teal">${parseFloat(ing.value).toFixed(4)}%</td>
                                                <td class="text-end pe-3">${parseFloat(ing.weight).toFixed(2)}g</td>
                                            </tr>
                                        `).join('')}
                                    </tbody>
                                </table>
                            </div>
                        `).join('') : '<p class="text-muted small text-center my-3">No formulas found for this CMF.</p>'}
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