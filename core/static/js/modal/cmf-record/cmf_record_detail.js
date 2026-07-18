$(document).ready(function() {
    let modalTable;

    // 1. Template for the FORMULA (Child Row)
    function formatFormulaRow(d) {
        let formulaRows = '';
        
        if (d.formulas && d.formulas.length > 0) {
            d.formulas.forEach(f => {
                formulaRows += `
                    <tr>
                        <td>${f.ingredient}</td>
                        <td class="text-end">${f.percentage}%</td>
                        <td class="text-end">${f.grams}g</td>
                        <td><span class="badge bg-secondary">${f.batch_no}</span></td>
                    </tr>`;
            });
        } else {
            formulaRows = '<tr><td colspan="4" class="text-center text-muted">No formulas found for this revision.</td></tr>';
        }

        return `
            <div class="formula-sub-table-container shadow-sm">
                <div class="mb-2 fw-bold small text-primary text-uppercase">
                    <i class="bi bi-flask-fill me-1"></i> Formula Composition
                </div>
                <table class="table table-sm table-bordered formula-sub-table">
                    <thead class="table-dark">
                        <tr>
                            <th>Ingredient</th>
                            <th class="text-end">Percentage (%)</th>
                            <th class="text-end">Grams (g)</th>
                            <th>Batch No.</th>
                        </tr>
                    </thead>
                    <tbody>${formulaRows}</tbody>
                </table>
            </div>`;
    }

    // 2. Initialize DataTables inside Modal
    modalTable = $('#modalDataTable').DataTable({
        columns: [
            {
                className: 'dt-control',
                orderable: false,
                data: null,
                defaultContent: '<i class="bi bi-plus-square"></i>',
            },
            { data: 'no' },
            { data: 'customer' },
            { data: 'color' },
            { data: 'status' },
            { data: 'date' }
        ],
        paging: false,
        info: false,
        searching: false,
        responsive: true
    });

    // 3. Trigger Modal from Main Table (cmf_records.html)
    $(document).on('click', '.record-row', function() {
        const cmfNo = $(this).find('td[data-col-index="0"]').text().trim();
        
        // Show the modal
        const myModal = new bootstrap.Modal(document.getElementById('cmfDetailModal'));
        myModal.show();
        
        document.getElementById('modalTitle').innerText = `History for CMF: ${cmfNo}`;

        // Fetch Data Simulation (Replace this with an actual AJAX call if needed)
        // This is where you'd fetch all records matching that CMF No.
        const mockRecords = [
            {
                no: cmfNo,
                customer: $(this).find('td[data-col-index="1"]').text(),
                color: $(this).find('td[data-col-index="2"]').text(),
                status: $(this).find('td[data-col-index="9"]').text().trim(),
                date: $(this).find('td[data-col-index="10"]').text(),
                formulas: [
                    { ingredient: "Pigment Blue 15:3", percentage: 5.20, grams: 52, batch_no: "LOT-ABC" },
                    { ingredient: "Titanium Dioxide", percentage: 94.80, grams: 948, batch_no: "LOT-XYZ" }
                ]
            }
        ];

        modalTable.clear().rows.add(mockRecords).draw();
    });

    // 4. Handle Sub-Row (Formula) click inside the Modal
    $('#modalDataTable tbody').on('click', 'td.dt-control', function (e) {
        e.stopPropagation();
        let tr = $(this).closest('tr');
        let row = modalTable.row(tr);

        if (row.child.isShown()) {
            row.child.hide();
            tr.removeClass('shown');
        } else {
            row.child(formatFormulaRow(row.data())).show();
            tr.addClass('shown');
        }
    });
});