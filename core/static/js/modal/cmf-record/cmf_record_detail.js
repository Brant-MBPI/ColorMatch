$(document).ready(function() {
    let modalTable;

    // 1. Template for the Child Row (Formulas)
    function formatFormulas(d) {
        let rowsHtml = '';
        
        if (d.formulas && d.formulas.length > 0) {
            d.formulas.forEach(f => {
                rowsHtml += `
                    <tr>
                        <td>${f.ingredient}</td>
                        <td class="text-end">${f.percentage}%</td>
                        <td class="text-end">${f.grams}g</td>
                        <td><code>${f.batch_no}</code></td>
                    </tr>`;
            });
        } else {
            rowsHtml = '<tr><td colspan="4" class="text-center text-muted">No formulas linked.</td></tr>';
        }

        return `
            <div class="formula-container shadow-sm">
                <div class="d-flex align-items-center mb-2">
                    <i class="bi bi-flask-fill text-info me-2"></i>
                    <span class="fw-bold small">Formula Breakdown for ${d.no}</span>
                </div>
                <table class="table table-sm table-bordered formula-table">
                    <thead class="table-light">
                        <tr class="extra-small text-uppercase">
                            <th>Ingredient</th>
                            <th class="text-end">Percentage</th>
                            <th class="text-end">Grams</th>
                            <th>Batch Code</th>
                        </tr>
                    </thead>
                    <tbody>${rowsHtml}</tbody>
                </table>
            </div>`;
    }

    // 2. Initialize DataTable inside Modal
    modalTable = $('#modalDataTable').DataTable({
        columns: [
            {
                className: 'dt-control',
                orderable: false,
                data: null,
                defaultContent: '<i class="bi bi-plus-square-fill"></i>',
            },
            { data: 'no' },
            { data: 'customer' },
            { data: 'primary_color' },
            { data: 'status' },
            { data: 'submitted_date' }
        ],
        paging: false,
        info: false,
        searching: false,
        responsive: true
    });

    // 3. Main Row Click Event
    // We target the main table's record-rows
    $(document).on('click', '.record-row', function() {
        const row = $(this);
        const cmfNo = row.find('td[data-col-index="0"]').text().trim();
        
        // Show Modal
        const myModal = new bootstrap.Modal(document.getElementById('cmfDetailModal'));
        myModal.show();

        // AJAX Simulation: Load your data here
        // In production: $.getJSON('/url/', {cmf_no: cmfNo}, function(data) { ... });
        const mockData = [{
            no: cmfNo,
            customer: row.find('td[data-col-index="1"]').text(),
            primary_color: row.find('td[data-col-index="2"]').text(),
            status: row.find('td[data-col-index="9"]').text().trim(),
            submitted_date: row.find('td[data-col-index="10"]').text(),
            formulas: [
                { ingredient: "Titanium Dioxide", percentage: 12.5, grams: 125, batch_no: "BT-2024" },
                { ingredient: "Carbon Black", percentage: 2.0, grams: 20, batch_no: "BK-009" },
                { ingredient: "Clear Resin Base", percentage: 85.5, grams: 855, batch_no: "RS-881" }
            ]
        }];

        modalTable.clear().rows.add(mockData).draw();
    });

    // 4. Expansion logic (Internal Modal Table)
    $('#modalDataTable tbody').on('click', 'td.dt-control', function (e) {
        e.stopPropagation();
        let tr = $(this).closest('tr');
        let row = modalTable.row(tr);

        if (row.child.isShown()) {
            row.child.hide();
            tr.removeClass('shown');
            $(this).html('<i class="bi bi-plus-square-fill"></i>');
        } else {
            row.child(formatFormulas(row.data())).show();
            tr.addClass('shown');
            $(this).html('<i class="bi bi-dash-square-fill"></i>');
        }
    });
});