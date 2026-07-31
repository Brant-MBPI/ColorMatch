from datetime import datetime
from django.views.decorators.http import require_POST
from django.db import transaction
from django.core.cache import cache
from django.http import JsonResponse
from main.utils.log_audit_trail import log_audit
from ...models import (
    tbl_cmf, tbl_cmf_formula, tbl_cmf_dates, 
    tbl_cmf_pending_completed, tbl_cmf_salesman, tbl_dc_extruder_formula, tbl_dc_extruder_formula02, tbl_internal_color_code, tbl_mb_extruder_formula, tbl_mb_extruder_formula02, tbl_resin, tbl_rm_incoming, tbl_rs
)

def get_salesman_list():
    data = cache.get('salesman_list')
    if not data:
        # If not there, get from DB and save for 1 day
        data = list(tbl_cmf_salesman.objects.all().order_by('name'))
        cache.set('salesman_list', data, 86400)
    return data

def get_color_list():
    data = cache.get('color_list')
    if not data:
        data = list(tbl_internal_color_code.objects.all().order_by('color'))
        cache.set('color_list', data, 86400)
    return data

def get_resin_list():
    data = cache.get('resin_list')
    if not data:
        data = list(tbl_resin.objects.filter(is_deleted=False).order_by('abbreviation'))
        cache.set('resin_list', data, 86400)
    return data

def get_cmf_records():
    cached_data = cache.get('cmf_records_list')
    if cached_data is not None:
        return cached_data

    # Added 'code' to select_related for efficiency
    status_records = tbl_cmf_pending_completed.objects.filter(
        cm_no__isnull=False
    ).select_related('cm_no', 'code').order_by('-cm_no')
    
    results = []
    for entry in status_records:
        cmf = entry.cm_no
        formula = tbl_cmf_formula.objects.filter(cm_no=cmf.cm_no).first()
        dates = tbl_cmf_dates.objects.filter(cm_no=cmf.cm_no).first()

        results.append({
            "id": cmf.cm_no,
            "no": cmf.cm_no,
            "customer": formula.customer if formula else "---",
            "primary_color": cmf.in_code_no.color if cmf.in_code_no else "---",
            "description": cmf.color_desc or "---",
            "product": formula.finished_product if formula else "---",
            "required_date": dates.date_required if dates else "---",
            "target_date": dates.due_date_lab.strftime('%m/%d/%y') if (dates and dates.due_date_lab) else "---",
            "type": cmf.matching_type or "---",
            "colorant_type": cmf.colorant_type or "---",
            # Updated: Access string via the new 'code' ForeignKey
            "code": entry.code.product_code if entry.code else "---",
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

    # Added 'code' to select_related
    status_records = tbl_cmf_pending_completed.objects.filter(
        rs_no__isnull=False
    ).select_related('rs_no', 'code').order_by('-rs_no')
    
    results = []
    for entry in status_records:
        rs = entry.rs_no
        dates = tbl_cmf_dates.objects.filter(rs_no=rs).first()

        results.append({
            "id": rs.id,
            "no": rs.rs_no,
            "customer": rs.customer or "---",
            "primary_color": rs.primary_color or "---",
            "description": rs.color_desc or "---",
            "product": rs.finished_product or "---",
            "required_date": dates.date_required if dates else "---",
            "target_date": dates.due_date_lab.strftime('%m/%d/%y') if (dates and dates.due_date_lab) else "---",
            "type": rs.matching_type or "---",
            "colorant_type": rs.colorant_type or "---",
            # Updated: Access string via the new 'code' ForeignKey
            "code": entry.code.product_code if entry.code else "---",
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


@require_POST
def toggle_final_formula(request, formula_type, formula_id):
    model = tbl_mb_extruder_formula if formula_type == 'mb' else tbl_dc_extruder_formula
    
    # Optimization: select_related parent objects so audit log doesn't trigger extra DB hits
    header = model.objects.filter(pk=formula_id).select_related('code', 'cm_no', 'rs_no').first()

    if not header:
        return JsonResponse({'success': False, 'error': 'Formula record not found.'}, status=404)

    with transaction.atomic():
        if header.is_final:
            # 1. REMOVE FINAL STATUS
            header.is_final = False
            header.save(update_fields=['is_final'])
            is_final_now = False
            new_status_code = None
        else:
            # 2. SET AS FINAL
            # Unset any other formula marked final for the SAME parent record
            if header.cm_no_id:
                model.objects.filter(cm_no=header.cm_no).exclude(pk=header.pk).update(is_final=False)
            elif header.rs_no_id:
                model.objects.filter(rs_no=header.rs_no).exclude(pk=header.pk).update(is_final=False)

            header.is_final = True
            header.save(update_fields=['is_final'])
            is_final_now = True
            new_status_code = header.code

        # --- UPDATE PENDING/COMPLETED STATUS RECORD ---
        # We perform the update directly on the queryset. 
        # No need to fetch 'status_record' into a variable first.
        if header.cm_no_id:
            tbl_cmf_pending_completed.objects.filter(cm_no=header.cm_no).update(code=new_status_code)
        elif header.rs_no_id:
            tbl_cmf_pending_completed.objects.filter(rs_no=header.rs_no).update(code=new_status_code)

        # --- PREPARE AUDIT MESSAGE ---
        # Determine formula identifier (Lot for MB, Product Code for DC)
        if formula_type == 'mb':
            formula_id_display = f"Lot: {header.lot_no or 'N/A'}"
        else:
            formula_id_display = f"Code: {header.code.product_code if header.code else 'N/A'}"

        # Determine parent identifier (CMF No or RS No)
        parent_display = header.cm_no.cm_no if header.cm_no else (header.rs_no.rs_no if header.rs_no else "Unknown")

        action = "Marked" if is_final_now else "Unmarked"
        audit_msg = f"{action} {formula_type.upper()} formula ({formula_id_display}) as Final for {parent_display}."

        log_audit(request, "Updated", audit_msg)

    # Clear caches
    cache.delete('cmf_records_list')
    cache.delete('rs_records_list')
    
    return JsonResponse({'success': True, 'is_final': is_final_now})