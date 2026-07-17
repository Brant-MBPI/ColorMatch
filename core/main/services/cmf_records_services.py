from main.models import tbl_cmf_dates, tbl_cmf_formula, tbl_cmf_pending_completed


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
    Fetches real CMF records by joining tbl_cmf, formula, dates, and pending status.
    """
    # We query the status table and 'follow' the relationships
    # .select_related optimizes the query (JOIN)
    status_records = tbl_cmf_pending_completed.objects.filter(cm_no__isnull=False).select_related('cm_no')

    results = []
    for entry in status_records:
        cmf = entry.cm_no
        # Fetch related formula and dates for this specific cm_no
        formula = tbl_cmf_formula.objects.filter(cm_no=cmf.cm_no).first()
        dates = tbl_cmf_dates.objects.filter(cm_no=cmf.cm_no).first()

        results.append({
            "no": cmf.cm_no,
            "customer": formula.customer if formula else "---",
            "primary_color": cmf.primary_color or "---",
            "description": cmf.color_desc or "---",
            "product": formula.finished_product if formula else "---",
            "required_date": dates.date_required if dates else "---",
            # Formatting date objects to string MM/DD/YY
            "target_date": dates.due_date_lab.strftime('%m/%d/%y') if (dates and dates.due_date_lab) else "---",
            "type": cmf.matching_type or "---",
            "code": entry.prod_code or "---",
            "status": "Completed" if entry.is_completed else "Pending",
            "submitted_date": entry.date_submitted.strftime('%m/%d/%y') if entry.date_submitted else "",
            "ar_no": entry.ar_no or "",
            "reason": entry.reason or "",
        })
    
    # Sort by No. descending
    return sorted(results, key=lambda x: x['no'], reverse=True)


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




# from datetime import datetime
# from main.models import (
#     tbl_cmf, tbl_cmf_formula, tbl_cmf_dates, 
#     tbl_cmf_pending_completed, tbl_rs
# )

# # Keep your header and column definitions as they are
# ALL_HEADERS = [
#     "No.", "Customer", "Primary Color", "Color Description",
#     "Finished Product", "Required Date", "Target Date", "Matching Type",
#     "Product Code", "Status", "Submitted Date", "AR No.", "Reason"
# ]

# COLS_BOTH = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
# COLS_COMPLETED = [0, 1, 2, 3, 4, 7, 8, 10, 11]
# COLS_PENDING = [0, 1, 2, 3, 4, 5, 6, 7, 12]

# def get_cmf_records():
#     """
#     Fetches real CMF records by joining tbl_cmf, formula, dates, and pending status.
#     """
#     # We query the status table and 'follow' the relationships
#     # .select_related optimizes the query (JOIN)
#     status_records = tbl_cmf_pending_completed.objects.filter(cm_no__isnull=False).select_related('cm_no')

#     results = []
#     for entry in status_records:
#         cmf = entry.cm_no
#         # Fetch related formula and dates for this specific cm_no
#         formula = tbl_cmf_formula.objects.filter(cm_no=cmf.cm_no).first()
#         dates = tbl_cmf_dates.objects.filter(cm_no=cmf.cm_no).first()

#         results.append({
#             "no": cmf.cm_no,
#             "customer": formula.customer if formula else "---",
#             "primary_color": cmf.primary_color or "---",
#             "description": cmf.color_desc or "---",
#             "product": formula.finished_product if formula else "---",
#             "required_date": dates.date_required if dates else "---",
#             # Formatting date objects to string MM/DD/YY
#             "target_date": dates.due_date_lab.strftime('%m/%d/%y') if (dates and dates.due_date_lab) else "---",
#             "type": cmf.matching_type or "---",
#             "code": entry.prod_code or "---",
#             "status": "Completed" if entry.is_completed else "Pending",
#             "submitted_date": entry.date_submitted.strftime('%m/%d/%y') if entry.date_submitted else "",
#             "ar_no": entry.ar_no or "",
#             "reason": entry.reason or "",
#         })
    
#     # Sort by No. descending
#     return sorted(results, key=lambda x: x['no'], reverse=True)

# def get_rs_records():
#     """
#     Fetches real RS records from tbl_rs and tbl_cmf_pending_completed.
#     """
#     status_records = tbl_cmf_pending_completed.objects.filter(rs_no__isnull=False).select_related('rs_no')

#     results = []
#     for entry in status_records:
#         rs = entry.rs_no
#         results.append({
#             "no": rs.rs_no,
#             "customer": rs.customer or "---",
#             "primary_color": rs.primary_color or "---",
#             "description": rs.color_desc or "---",
#             "product": rs.finished_product or "---",
#             "required_date": rs.date_required or "---",
#             "target_date": rs.due_date.strftime('%m/%d/%y') if rs.due_date else "---",
#             "type": rs.matching_type or "---",
#             "code": entry.prod_code or "---",
#             "status": "Completed" if entry.is_completed else "Pending",
#             "submitted_date": entry.date_submitted.strftime('%m/%d/%y') if entry.date_submitted else "",
#             "ar_no": entry.ar_no or "",
#             "reason": entry.reason or "",
#         })
#     return results

# def get_active_columns(show_completed, show_pending):
#     if show_completed and show_pending:
#         return COLS_BOTH
#     elif show_completed:
#         return COLS_COMPLETED
#     elif show_pending:
#         return COLS_PENDING
#     return []

# def get_filtered_records(mode, show_completed, show_pending):
#     source = get_rs_records() if mode == 'rs' else get_cmf_records()

#     if show_completed and show_pending:
#         return source
#     elif show_completed:
#         return [r for r in source if r['status'] == 'Completed']
#     elif show_pending:
#         return [r for r in source if r['status'] == 'Pending']
#     return []