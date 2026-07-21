from datetime import datetime
from django.core.cache import cache
from django.http import JsonResponse
from ...models import (
    tbl_cmf, tbl_cmf_formula, tbl_cmf_dates, 
    tbl_cmf_pending_completed, tbl_dc_extruder_formula, tbl_dc_extruder_formula02, tbl_mb_extruder_formula, tbl_mb_extruder_formula02, tbl_rm_incoming, tbl_rs
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

def get_raw_material_codes():
    """
    Fetches all unique material codes from tbl_rm_incoming.
    Uses caching to avoid heavy database hits.
    """
    cache_key = 'raw_material_codes'
    materials = cache.get(cache_key)

    if materials is None:
        # We use values_list with flat=True to get a simple list of strings
        # We use distinct() to avoid duplicates and order_by for easier searching in UI
        materials = list(
            tbl_rm_incoming.objects.values_list('material_code', flat=True)
            .distinct()
            .order_by('material_code')
        )
        
        # Cache the result for 1 hour (3600 seconds)
        cache.set(cache_key, materials, 3600)

    return materials

def get_all_records_combined():
    """
    Returns all CMF and RS records loaded once for instant JS filtering.
    """
    return get_cmf_records() + get_rs_records()


def get_cmf_formulas(request, cm_no):
    # 1. Get Parent CMF Info
    cmf = tbl_cmf.objects.filter(cm_no=cm_no).first()
    if not cmf:
        return JsonResponse([], safe=False)

    # Fetch extra details from related tables
    formula_info = tbl_cmf_formula.objects.filter(cm_no=cm_no).first()
    pending_info = tbl_cmf_pending_completed.objects.filter(cm_no=cm_no).first()

    # 2. Process MB Formulas
    mb_list = []
    # select_related('code') joins the tbl_generated_prod_code table
    mb_qs = tbl_mb_extruder_formula.objects.filter(cm_no=cm_no).select_related('code', 'cm_no__in_code_no')
    
    for h in mb_qs:
        # Fetch ingredients and convert Decimals to floats manually
        ingredients = []
        for ing in tbl_mb_extruder_formula02.objects.filter(mb=h):
            ingredients.append({
                'material': ing.material or '---',
                'value': float(ing.value) if ing.value is not None else 0,
                'weight': float(ing.weight) if ing.weight is not None else 0
            })
        
        mb_list.append({
            'date': h.date.strftime('%m/%d/%y') if h.date else '---',
            'prod_code': h.code.prod_code if h.code else '---',
            'lot_no': h.lot_no or '---',
            'color': h.cm_no.in_code_no.color if (h.cm_no and h.cm_no.in_code_no) else '---',
            'mixing_time': h.mixing_time or '---',
            'matched_by': h.matched_by or '---',
            'ingredients': ingredients
        })

    # 3. Process DC Formulas
    dc_list = []
    dc_qs = tbl_dc_extruder_formula.objects.filter(cm_no=cm_no).select_related('code', 'cm_no__in_code_no')
    
    for h in dc_qs:
        ingredients = []
        for ing in tbl_dc_extruder_formula02.objects.filter(dc=h):
            ingredients.append({
                'material': ing.material or '---',
                'value': float(ing.value) if ing.value is not None else 0,
                'weight': float(ing.weight) if ing.weight is not None else 0
            })
            
        dc_list.append({
            'date': h.date.strftime('%m/%d/%y') if h.date else '---',
            'prod_code': h.code.prod_code if h.code else '---',
            'color': h.cm_no.in_code_no.color if (h.cm_no and h.cm_no.in_code_no) else '---',
            'sample_size': h.sample_size or '---',
            'mixing_time': h.mixing_time or '---',
            'matched_by': h.matched_by or '---',
            'ingredients': ingredients
        })

    # 4. Final Data Structure
    results = [{
        'cm_no': cmf.cm_no,
        'customer': formula_info.customer if formula_info else '---',
        'color': cmf.in_code_no.color if cmf.in_code_no else '---',
        'type': cmf.matching_type or '---',
        'code': pending_info.prod_code if pending_info else '---',
        'status': ("Completed" if pending_info.is_completed else "Pending") if pending_info else "Pending",
        'mb_formulas': mb_list,
        'dc_formulas': dc_list
    }]

    return JsonResponse(results, safe=False)