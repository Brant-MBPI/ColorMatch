/**
 * PRO-TIP: We use "Event Delegation" by attaching the listener to the <tbody>.
 * This ensures it works even if you refresh the table data via AJAX.
 */
document.addEventListener('DOMContentLoaded', function () {
    const recordsTbody = document.getElementById('recordsTbody');
    const modalElement = document.getElementById('cmfDetailModal');
    
    // Initialize the Bootstrap Modal object
    const bsModal = new bootstrap.Modal(modalElement);
    let modalDt = null; // To store the DataTables instance

    // --- TRIGGER POINT ---
    recordsTbody.addEventListener('dblclick', function (e) {
        // Find the closest row to the element clicked
        const tr = e.target.closest('.record-row');
        
        if (tr) {
            // 1. Get the CMF No from the first cell (index 0)
            const cmfNo = tr.cells[0].innerText.trim();
            const customer = tr.cells[1].innerText.trim();
            const color = tr.cells[2].innerText.trim();
            const status = tr.cells[9].innerText.trim();

            // 2. Open the Modal
            bsModal.show();

            // 3. Setup the Modal DataTable
            setupModalTable(cmfNo, customer, color, status);
        }
    });

    // Function to handle the table inside the modal
    function setupModalTable(cmfNo, customer, color, status) {
        const tableId = '#modalDataTable';

        // Destroy existing table if it exists to refresh data
        if (modalDt) {
            modalDt.destroy();
        }

        // Initialize Vanilla DataTables (v2.0+)
        modalDt = new DataTable(tableId, {
            data: [{ // Mock data - usually you'd fetch this from the server
                no: cmfNo,
                customer: customer,
                color: color,
                status: status,
                formulas: [
                    { mat: "Pigment A", pct: "10.00", qty: "100.00", lot: "B100" },
                    { mat: "Resin B", pct: "90.00", qty: "900.00", lot: "R500" }
                ]
            }],
            columns: [
                {
                    className: 'dt-control',
                    orderable: false,
                    data: null,
                    defaultContent: '<i class="bi bi-plus-circle text-primary"></i>'
                },
                { data: 'no' },
                { data: 'customer' },
                { data: 'color' },
                { data: 'status' }
            ],
            paging: false,
            searching: false,
            info: false
        });

        // Handle the Sub-Row (Formula) click
        modalDt.on('click', 'td.dt-control', function (e) {
            let tr = e.target.closest('tr');
            let row = modalDt.row(tr);

            if (row.child.isShown()) {
                row.child.hide();
                e.target.innerHTML = '<i class="bi bi-plus-circle text-primary"></i>';
            } else {
                row.child(formatFormula(row.data())).show();
                e.target.innerHTML = '<i class="bi bi-dash-circle text-danger"></i>';
            }
        });
    }

    // Helper: HTML structure for the formula sub-row
    function formatFormula(d) {
        let rows = d.formulas.map(f => `
            <tr>
                <td>${f.mat}</td>
                <td class="text-end">${f.pct}%</td>
                <td class="text-end">${f.qty}g</td>
                <td><span class="badge bg-secondary">${f.lot}</span></td>
            </tr>
        `).join('');

        return `
            <div class="formula-details shadow-sm border rounded p-3">
                <table class="table table-sm mb-0">
                    <thead class="small text-uppercase bg-light">
                        <tr><th>Material</th><th class="text-end">%</th><th class="text-end">Qty</th><th>Lot</th></tr>
                    </thead>
                    <tbody class="small">${rows}</tbody>
                </table>
            </div>`;
    }
});