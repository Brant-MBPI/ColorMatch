ALL_HEADERS = [
    "No.", "Customer", "Primary Color", "Color Description",
    "Finished Product", "Required Date", "Target Date", "Matching Type",
    "Product Code", "Status", "Submitted Date", "AR No.", "Reason"
]

COLS_BOTH = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
COLS_COMPLETED = [0, 1, 2, 3, 4, 7, 8, 10, 11]
COLS_PENDING = [0, 1, 2, 3, 4, 5, 6, 7, 12]


def get_cmf_records():
    """
    Fetches CMF records fresh on every call.
    Replace the hardcoded list below with a real DB query later, e.g.:
        return list(CMFRecord.objects.values(
            'no', 'customer', 'primary_color', 'description', 'product',
            'required_date', 'target_date', 'type', 'code', 'status',
            'submitted_date', 'ar_no', 'reason'
        ))
    """
    return [
        {
            "no": "A8722a", "customer": "Masterbatch PH", "primary_color": "Red",
            "description": "Gloss", "product": "Cap", "required_date": "10/25/24",
            "target_date": "10/30/24", "type": "New", "code": "PC-001",
            "status": "Completed", "submitted_date": "10/29/24", "ar_no": "AR-1001", "reason": "",
        },
        {
            "no": "A8735a", "customer": "Generic Co.", "primary_color": "Blue",
            "description": "Matte", "product": "Tray", "required_date": "11/01/24",
            "target_date": "11/05/24", "type": "Re-Match", "code": "PC-002",
            "status": "Pending", "submitted_date": "", "ar_no": "", "reason": "Awaiting resin sample",
        },
        {
            "no": "A8735b", "customer": "Generic Co.", "primary_color": "Blue",
            "description": "Matte", "product": "Tray", "required_date": "11/01/24",
            "target_date": "11/05/24", "type": "Re-Match", "code": "PC-002",
            "status": "Completed", "submitted_date": "11/04/24", "ar_no": "AR-1002", "reason": "",
        },
        {
            "no": "A8801a", "customer": "Plasti-Wrap Corp", "primary_color": "Green",
            "description": "Translucent", "product": "Bottle", "required_date": "11/10/24",
            "target_date": "11/15/24", "type": "New", "code": "PC-003",
            "status": "Pending", "submitted_date": "", "ar_no": "", "reason": "Pending customer approval",
        },
        {
            "no": "A8812a", "customer": "Nova Packaging", "primary_color": "Black",
            "description": "Opaque", "product": "Closure", "required_date": "11/12/24",
            "target_date": "11/18/24", "type": "Re-Match", "code": "PC-004",
            "status": "Completed", "submitted_date": "11/17/24", "ar_no": "AR-1003", "reason": "",
        },
    ]


def get_rs_records():
    """
    Fetches RS records fresh on every call.
    Replace the hardcoded list below with a real DB query later, e.g.:
        return list(RSRecord.objects.values(
            'no', 'customer', 'primary_color', 'description', 'product',
            'required_date', 'target_date', 'type', 'code', 'status',
            'submitted_date', 'ar_no', 'reason'
        ))
    """
    return [
        {
            "no": "RS-3301", "customer": "Masterbatch PH", "primary_color": "Red",
            "description": "Gloss", "product": "Cap", "required_date": "10/20/24",
            "target_date": "10/28/24", "type": "New", "code": "PC-001",
            "status": "Completed", "submitted_date": "10/27/24", "ar_no": "AR-2001", "reason": "",
        },
        {
            "no": "RS-3312", "customer": "Generic Co.", "primary_color": "Blue",
            "description": "Matte", "product": "Tray", "required_date": "10/29/24",
            "target_date": "11/03/24", "type": "Re-Match", "code": "PC-002",
            "status": "Pending", "submitted_date": "", "ar_no": "", "reason": "Waiting for lab result",
        },
        {
            "no": "RS-3320", "customer": "Plasti-Wrap Corp", "primary_color": "Green",
            "description": "Translucent", "product": "Bottle", "required_date": "11/08/24",
            "target_date": "11/14/24", "type": "New", "code": "PC-003",
            "status": "Completed", "submitted_date": "11/13/24", "ar_no": "AR-2002", "reason": "",
        },
        {
            "no": "RS-3325", "customer": "Nova Packaging", "primary_color": "Black",
            "description": "Opaque", "product": "Closure", "required_date": "11/11/24",
            "target_date": "11/16/24", "type": "Re-Match", "code": "PC-004",
            "status": "Pending", "submitted_date": "", "ar_no": "", "reason": "Awaiting AR submission",
        },
    ]


def get_active_columns(show_completed, show_pending):
    if show_completed and show_pending:
        return COLS_BOTH
    elif show_completed:
        return COLS_COMPLETED
    elif show_pending:
        return COLS_PENDING
    return []


def get_filtered_records(mode, show_completed, show_pending):
    """
    Single entry point the view calls: handles mode selection (CMF vs RS)
    and status filtering in one place.
    """
    source = get_rs_records() if mode == 'rs' else get_cmf_records()

    if show_completed and show_pending:
        return source
    elif show_completed:
        return [r for r in source if r['status'] == 'Completed']
    elif show_pending:
        return [r for r in source if r['status'] == 'Pending']
    return []