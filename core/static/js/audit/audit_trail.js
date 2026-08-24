jQuery(document).ready(function($) {
    const tableId = '#auditTable';
    
    const table = $(tableId).DataTable({
        serverSide: true,
        processing: true,
        destroy: true,
        deferRender: true,
        scrollY: '58vh', // Adjusted for pagination space
        scrollCollapse: true,
        ajax: {
            url: "/audit-trail/data/",
            type: "GET",
            data: function(d) {
                d.department = $('#filterDept').val();
                d.column_choice = $('#filterCol').val(); // Send selected column
                d.date_from = $('#dateFrom').val();
                d.date_to = $('#dateTo').val();
            }
        },
        columns: [
            { data: "timestamp", className: "ps-3 text-nowrap" },
            { data: "username", className: "fw-bold text-teal" },
            { data: "full_name" },
            { 
                data: "action_type",
                render: function(data) {
                    let cls = "bg-secondary-subtle text-secondary";
                    
                    if (['Saved', 'Created'].includes(data)) {
                        cls = "bg-success-subtle text-success border-success-subtle";
                    }
                    else if (data.includes('Updated') || data === 'MODIFY') {
                        cls = "bg-primary-subtle text-primary border-primary-subtle";
                    }
                    else if (data === 'Deleted') {
                        cls = "bg-danger-subtle text-danger border-danger-subtle";
                    }
                    // NEW: Style for Printed
                    else if (data === 'Printed') {
                        // Using Info (Cyan) which looks professional for document actions
                        cls = "bg-info-subtle text-info border-info-subtle"; 
                    }
                    
                    return `<span class="badge ${cls} border px-2">${data}</span>`;
                }
            },
            { 
                data: "details", 
                className: "text-wrap",
                render: function(data) {
                    return `<div style="min-width: 300px; max-width: 600px;">${data || '---'}</div>`;
                }
            },
            { data: "email" },
            { data: "department", className: "pe-3" }
        ],
        dom: 'rtp', // Shows processing, table, and pagination at bottom
        pageLength: 100,
        ordering: false,
        language: {
            processing: '<div class="d-flex justify-content-center py-4"><div class="spinner-border text-teal"></div></div>',
            paginate: {
                previous: '<i class="bi bi-chevron-left"></i>',
                next: '<i class="bi bi-chevron-right"></i>'
            }
        },
        drawCallback: function(settings) {
            const api = this.api();
            const info = api.page.info();
            const total = info.recordsTotal.toLocaleString();
            const filtered = info.recordsDisplay.toLocaleString();
            
            if (info.recordsTotal === info.recordsDisplay) {
                $('#auditCountLabel').text(`${total} records total`);
            } else {
                $('#auditCountLabel').text(`${filtered} found (from ${total})`);
            }
        }
    });

    // 1. Search with debounce
    const handleSearch = debounce(function(value) {
        table.search(value).draw();
    }, 600);

    $('#auditSearch').on('input', function() {
        handleSearch(this.value);
    });

    // 2. Dropdown and Date listeners
    $('#filterDept, #filterCol, #dateFrom, #dateTo').on('change', function() {
        table.ajax.reload();
    });

    // 3. Refresh
    $('#btnRefreshAudit').on('click', () => table.ajax.reload());

    // 4. Export
    $('#btnExportAudit').on('click', function() {
        const dateFrom = $('#dateFrom').val();
        const dateTo = $('#dateTo').val();
        const dept = $('#filterDept').val();

        // Determine the confirmation message
        let rangeMsg = `Export records from ${dateFrom} to ${dateTo}?`;
        if (dept !== 'all') {
            rangeMsg += `Filtering by Department: ${dept}`;
        }

        Preline.confirm(
            'Confirm Excel Export',
            rangeMsg,
            'success',
            () => {
                // This runs if the user clicks "Confirm"
                const params = $.param({
                    department: $('#filterDept').val(),
                    column_choice: $('#filterCol').val(),
                    date_from: dateFrom,
                    date_to: dateTo,
                    search: $('#auditSearch').val()
                });

                // Show global loader if available
                if (typeof showLoader === "function") showLoader();

                // Trigger download
                window.location.href = `/audit-trail/export/?${params}`;

                // Hide loader after a delay
                setTimeout(() => {
                    if (typeof hideLoader === "function") hideLoader();
                }, 3000);
            }
        );
    });
});