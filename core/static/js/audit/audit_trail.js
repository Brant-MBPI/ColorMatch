jQuery(document).ready(function($) {
    const table = $('#auditTable').DataTable({
        serverSide: true,
        processing: true,
        destroy: true, // Prevents errors on re-init
        ajax: {
            url: "/audit-trail/data/",
            type: "GET",
            data: function(d) {
                d.department = $('#filterDept').val();
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
                    if (['Saved', 'Created'].includes(data)) cls = "bg-success-subtle text-success border-success-subtle";
                    else if (['Updated', 'MODIFY', 'Updated Master Formula Entry'].some(v => data.includes(v))) cls = "bg-primary-subtle text-primary border-primary-subtle";
                    else if (data === 'Deleted') cls = "bg-danger-subtle text-danger border-danger-subtle";
                    return `<span class="badge ${cls} border px-2">${data}</span>`;
                }
            },
            { 
                data: "details", 
                className: "text-wrap",
                render: function(data) {
                    return `<div style="min-width: 300px; max-width: 500px;">${data || '---'}</div>`;
                }
            },
            { data: "email" },
            { data: "department", className: "pe-3" }
        ],
        dom: 'rtp',
        pageLength: 100,
        ordering: false,
        language: {
            processing: '<div class="d-flex justify-content-center py-4"><div class="spinner-border text-teal"></div></div>',
            emptyTable: "No audit records found matching your criteria."
        },
        drawCallback: function(settings) {
            const api = this.api();
            const info = api.page.info();
            $('#auditCountLabel').text(`${info.recordsDisplay.toLocaleString()} records found`);
        }
    });

    // 1. Search with debounce
    let searchTimeout;
    $('#auditSearch').on('input', function() {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            table.search(this.value).draw();
        }, 400);
    });

    // 2. Filter triggers
    $('#filterDept, #dateFrom, #dateTo').on('change', function() {
        table.ajax.reload();
    });

    // 3. Refresh
    $('#btnRefreshAudit').on('click', function() {
        table.ajax.reload();
    });

    // 4. Export
    $('#btnExportAudit').on('click', function() {
        const params = $.param({
            department: $('#filterDept').val(),
            date_from: $('#dateFrom').val(),
            date_to: $('#dateTo').val(),
            search: $('#auditSearch').val()
        });
        window.location.href = `/audit-trail/export/?${params}`;
    });
});