from urllib import request

from django.shortcuts import render
from django.http import HttpResponse
# Create your views here.


ALL_HEADERS = [
    "No.", "Customer", "Primary Color", "Color Description",
    "Finished Product", "Required Date", "Target Date", "Matching Type",
    "Product Code", "Status", "Submitted Date", "AR No.", "Reason"
]

COLS_BOTH = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
COLS_COMPLETED = [0, 1, 2, 3, 4, 7, 8, 10, 11]
COLS_PENDING = [0, 1, 2, 3, 4, 5, 6, 7, 12]

CMF_RECORDS = [
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

RS_RECORDS = [
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


def get_cmf_records_active_columns(show_completed, show_pending):
    if show_completed and show_pending:
        return COLS_BOTH
    elif show_completed:
        return COLS_COMPLETED
    elif show_pending:
        return COLS_PENDING
    return []


def index(request):
    return render(request, "base.html")

def dashboard(request):
    return render(request, "sidemenu/dashboard/dashboard.html")

def otherPage(request):
    return render(request, "sidemenu/other.html")

def cmf_records(request):
    mode = request.GET.get('mode', 'cmf')
    show_completed = request.GET.get('completed', '1') == '1'
    show_pending = request.GET.get('pending', '1') == '1'

    source = RS_RECORDS if mode == 'rs' else CMF_RECORDS

    if show_completed and show_pending:
        records = source
    elif show_completed:
        records = [r for r in source if r['status'] == 'Completed']
    elif show_pending:
        records = [r for r in source if r['status'] == 'Pending']
    else:
        records = []

    active_cols = get_cmf_records_active_columns(show_completed, show_pending)

    context = {
        'records': records,
        'active_cols': active_cols,
        'col_no_label': "RS No." if mode == 'rs' else "CMF No.",
        'mode': mode,
        'show_completed': show_completed,
        'show_pending': show_pending,
    }

    return render(request, "sidemenu/cmf/cmf_records.html", context)

def cmf_entry(request):
    customers = [
        "Masterbatch PH",
        "Generic Co.",
    ]
    salesman = [
        "Brant Jan Abillanoza",
        "Francis Candedlaria",
    ]
    primary_color = [
        "Red",
        "Green",
        "Blue"
    ]
    resin = [
        "pp",
        "hdpe",
    ]

    
    return render(request, "sidemenu/cmf/cmf_entry.html", {
        "customers": customers,
        "salesman": salesman,
        "primary_color": primary_color,
        "resin": resin,
    })

def cmf_rs_entry(request):
    return render(request, "sidemenu/cmf/rs_entry.html")

def cmf_mb_formula(request):
    return render(request, "sidemenu/cmf/formula_mb.html")

def cmf_dc_formula(request):
    return render(request, "sidemenu/cmf/formula_dc.html")

def cmf_pending_completed(request):
    return render(request, "sidemenu/cmf/pending_completed.html")

def feedback(request):
    return render(request, "sidemenu/feedback/feedback.html")

def audit_trail(request):
    return render(request, "sidemenu/audit_trail.html")