from datetime import datetime
from django.core.cache import cache
from django.http import JsonResponse
from ...models import (
    tbl_cmf, tbl_cmf_formula, tbl_cmf_dates, 
    tbl_cmf_pending_completed, tbl_dc_extruder_formula, tbl_dc_extruder_formula02, tbl_mb_extruder_formula, tbl_mb_extruder_formula02, tbl_rs
)

ALL_HEADERS = [
    "No.", "Customer", "Primary Color", "Color Description",
    "Finished Product", "Required Date", "Target Date", "Matching Type",
    "Product Code", "Status", "Submitted Date", "AR No.", "Reason"
]


def get_cmf_records():
    cached_data = cache.get('cmf_records_list')
    if cached_data is not None:
        return cached_data

    status_records = tbl_cmf_pending_completed.objects.filter(cm_no__isnull=False).select_related('cm_no')
    results = []
    for entry in status_records:
        cmf = entry.cm_no
        formula = tbl_cmf_formula.objects.filter(cm_no=cmf.cm_no).first()
        dates = tbl_cmf_dates.objects.filter(cm_no=cmf.cm_no).first()

        results.append({
            "no": cmf.cm_no,
            "customer": formula.customer if formula else "---",
            "primary_color": cmf.in_code_no.color if cmf.in_code_no else "---",
            "description": cmf.color_desc or "---",
            "product": formula.finished_product if formula else "---",
            "required_date": dates.date_required if dates else "---",
            "target_date": dates.due_date_lab.strftime('%m/%d/%y') if (dates and dates.due_date_lab) else "---",
            "type": cmf.matching_type or "---",
            "code": entry.prod_code or "---",
            "status": "Completed" if entry.is_completed else "Pending",
            "submitted_date": entry.date_submitted.strftime('%m/%d/%y') if entry.date_submitted else "",
            "ar_no": entry.ar_no or "",
            "reason": entry.reason or "",
            "mode": "cmf"
        })
    
    final_results = sorted(results, key=lambda x: x['no'], reverse=True)
    cache.set('cmf_records_list', final_results, 3600)
    return final_results

def get_rs_records():
    cached_data = cache.get('rs_records_list')
    if cached_data is not None:
        return cached_data

    status_records = tbl_cmf_pending_completed.objects.filter(rs_no__isnull=False).select_related('rs_no')
    results = []
    for entry in status_records:
        rs = entry.rs_no
        results.append({
            "no": rs.rs_no,
            "customer": rs.customer or "---",
            "primary_color": rs.primary_color or "---",
            "description": rs.color_desc or "---",
            "product": rs.finished_product or "---",
            "required_date": rs.date_required or "---",
            "target_date": rs.due_date.strftime('%m/%d/%y') if rs.due_date else "---",
            "type": rs.matching_type or "---",
            "code": entry.prod_code or "---",
            "status": "Completed" if entry.is_completed else "Pending",
            "submitted_date": entry.date_submitted.strftime('%m/%d/%y') if entry.date_submitted else "",
            "ar_no": entry.ar_no or "",
            "reason": entry.reason or "",
            "mode": "rs"
        })
    
    cache.set('rs_records_list', results, 3600)
    return results

def get_all_records_combined():
    """
    Returns all CMF and RS records loaded once for instant JS filtering.
    """
    return get_cmf_records() + get_rs_records()


def get_cmf_formulas(request, cm_no):
    # 1. Get the Parent CMF Details first
    cmf = tbl_cmf.objects.filter(cm_no=cm_no).first()
    
    if not cmf:
        return JsonResponse([], safe=False)

    # 2. This is your EXACT logic for collecting formulas
    all_related_formulas = []

    # MB Formulas Logic (Your Code)
    mb_headers = tbl_mb_extruder_formula.objects.filter(cm_no=cm_no).select_related('code')
    for header in mb_headers:
        ingredients = tbl_mb_extruder_formula02.objects.filter(mb=header).values('material', 'value', 'weight')
        all_related_formulas.append({
            'type': 'MB Extruder',
            'formula_no': f"MB-{header.mb_no}",
            'lot_no': header.lot_no or '---',
            'matched_by': header.matched_by or '---',
            'date': header.date.strftime('%Y-%m-%d') if header.date else '---',
            'status': 'Completed',
            'ingredients': list(ingredients) # Your working conversion
        })

    # DC Formulas Logic (Your Code)
    dc_headers = tbl_dc_extruder_formula.objects.filter(cm_no=cm_no).select_related('code')
    for header in dc_headers:
        ingredients = tbl_dc_extruder_formula02.objects.filter(dc=header).values('material', 'value', 'weight')
        all_related_formulas.append({
            'type': 'DC Extruder',
            'formula_no': f"DC-{header.dc_no}",
            'lot_no': '---',
            'matched_by': header.matched_by or '---',
            'date': header.date.strftime('%Y-%m-%d') if header.date else '---',
            'status': 'Completed',
            'ingredients': list(ingredients) # Your working conversion
        })

    # 3. Structure the final response to have the CMF as the parent
    results = [{
        'cm_no': cmf.cm_no,
        'customer': cmf.customer or '---',
        'color': cmf.primary_color or '---',
        'type': cmf.matching_type or '---',
        'code': cmf.product_code or '---',
        'status': cmf.status or 'Pending',
        'formulas': all_related_formulas # Nesting your working formula list here
    }]

    return JsonResponse(results, safe=False)