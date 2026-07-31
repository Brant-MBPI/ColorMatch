from main.utils.log_audit_trail import log_audit
from django.db import transaction
from django.core.cache import cache
from main.models import (
    tbl_dc_extruder_formula, tbl_feedback_details, tbl_cmf, tbl_mb_extruder_formula, tbl_rs, tbl_cmf_pending_completed, tbl_cmf_formula, tbl_cmf_dates
)

CACHE_KEY = 'feedback_records_list'

def get_feedback_records():
    """Fetches the list of feedback records with unified metadata, using cache."""
    cached_data = cache.get(CACHE_KEY)
    if cached_data is not None:
        return cached_data

    feedback_qs = tbl_feedback_details.objects.all().select_related('cm_no', 'rs_no').order_by('-feedback_no')
    records_list = []

    for fb in feedback_qs:
        data = {
            'feedback_no': fb.feedback_no,
            'status': fb.status,
            'details': fb.comment or '---',
            'package_details': fb.storage_details or '---',
        }

        final_formula = None

        if fb.cm_no:
            # 1. Product Code from Final Formula logic
            final_formula = tbl_mb_extruder_formula.objects.filter(cm_no=fb.cm_no, is_final=True).select_related('code').first()
            if not final_formula:
                final_formula = tbl_dc_extruder_formula.objects.filter(cm_no=fb.cm_no, is_final=True).select_related('code').first()

            formula = tbl_cmf_formula.objects.filter(cm_no=fb.cm_no).first()
            dates = tbl_cmf_dates.objects.filter(cm_no=fb.cm_no).first()

            data.update({
                'matching_no': fb.cm_no.cm_no,
                'customer': formula.customer if formula else '---',
                'color_desc': fb.cm_no.color_desc or '---',
                'finished_prod': formula.finished_product if formula else '---',
                'required_date': dates.date_required if dates else '---',
                'due_date': dates.due_date_lab.strftime('%m/%d/%Y') if dates and dates.due_date_lab else '---',
                'type': fb.cm_no.matching_type or '---',
                'prod_code': final_formula.code.product_code if final_formula and final_formula.code else (fb.code_submitted or '---'),
                'mode': 'cmf'
            })

        elif fb.rs_no:
            # 2. RS Metadata logic
            pending_info = tbl_cmf_pending_completed.objects.filter(rs_no=fb.rs_no).select_related('code').first()
            dates = tbl_cmf_dates.objects.filter(rs_no=fb.rs_no).first()
            
            data.update({
                'matching_no': fb.rs_no.rs_no,
                'customer': fb.rs_no.customer or '---',
                'color_desc': fb.rs_no.color_desc or '---',
                'prod_code': pending_info.code.product_code if pending_info and pending_info.code else '---',
                'finished_prod': fb.rs_no.finished_product or '---',
                'required_date': dates.date_required if dates else '---',
                'due_date': dates.due_date_lab.strftime('%m/%d/%Y') if dates and dates.due_date_lab else '---',
                'type': fb.rs_no.matching_type or '---',
                'mode': 'rs'
            })

        records_list.append(data)

    cache.set(CACHE_KEY, records_list, 3600) # Cache for 1 hour
    return records_list

def update_feedback_entry(request):
    """Handles the POST request to update feedback details."""
    feedback_no = request.POST.get('feedback_no')
    status = request.POST.get('feedback_status')
    comments = request.POST.get('comments')
    storage = request.POST.get('storage_details')

    with transaction.atomic():
        fb = tbl_feedback_details.objects.get(feedback_no=feedback_no)
        fb.status = status
        fb.comment = comments
        fb.storage_details = storage
        fb.save()

        # Audit Log
        parent_no = fb.cm_no.cm_no if fb.cm_no else fb.rs_no.rs_no
        log_audit(request, "Updated", f"Updated feedback details for {parent_no}. Status: {status}")

        # Invalidate the cache
        cache.delete(CACHE_KEY)
    
    return fb