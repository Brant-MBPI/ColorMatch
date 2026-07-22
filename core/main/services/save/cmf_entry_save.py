import re
from django.db import transaction
from datetime import datetime
from main.utils.log_audit_trail import log_audit
from main.models import (
    tbl_cmf, tbl_cmf_color_req, tbl_cmf_dates, tbl_cmf_formula, 
    tbl_cmf_process, tbl_cmf_process02, tbl_resin, tbl_resins_selected,
    tbl_cmf_specification, tbl_cmf_specification02, tbl_cmf_salesman,
    tbl_cmf_pending_completed, tbl_feedback_details
)

def save_cmf_complete_entry(request):
    data = request.POST
    
    # --- 1. CLEAN AND VALIDATE LISTS FIRST ---
    # Browsers sometimes send [''] for empty selections. We filter those out.
    selected_resins = [r for r in data.getlist('resin') if r.strip()]
    selected_processes = [p for p in data.getlist('process') if p.strip()]
    selected_specs = [s for s in data.getlist('specification') if s.strip()]

    if not selected_resins:
        raise Exception("Selection Required: At least one Resin Type must be selected.")
    if not selected_processes:
        raise Exception("Selection Required: At least one Process must be selected.")

    # --- 2. STRICT TEXT VALIDATION ---
    required_fields = [
        'cmf_no', 'customer', 'date_created', 'required_date', 'date_received', 
        'due_date', 'matchType', 'salesman', 'finished_product', 'primary_color', 
        'color_description', 'colorReq', 'qty_resin_test', 'customerResin', 
        'mi_customer_resin', 'sampleColorant', 'colorantType', 'dosage', 
        'processing_temp', 'color_guide_return', 'is_low_cost'
    ]
    
    def clean_label(name):
        mapping = {
            'cmf_no': 'CMF No.', 'matchType': 'Matching Type', 'colorReq': 'Color Requirement',
            'qty_resin_test': 'Qty Resin for Test', 'customerResin': 'Customer Resin Provided',
            'mi_customer_resin': 'MI Customer Resin', 'sampleColorant': 'Sample Colorant Available',
            'colorantType': 'Colorant Type', 'is_low_cost': 'Is Low Cost'
        }
        return mapping.get(name, name.replace('_', ' ').title())

    for field in required_fields:
        val = data.get(field, '').strip()
        if not val:
            raise Exception(f"Field required: {clean_label(field)}. This cannot be empty.")

    # --- 3. HELPERS ---
    def to_bool(val):
        if val == 'Y': return True
        if val == 'N': return False
        return None

    def format_date(d_str):
        if not d_str or d_str.upper() == "ASAP": return None
        try:
            return datetime.strptime(d_str.split(',')[0].strip(), '%m/%d/%Y').strftime('%Y-%m-%d')
        except: return None

    def clean_numeric(val):
        if not val: return "0"
        return re.sub(r'[^\d.]', '', str(val))

    # --- 4. DATABASE TRANSACTION ---
    with transaction.atomic():
        # A. Lookup Salesman
        salesman_name = data.get('salesman').strip()
        salesman_obj = tbl_cmf_salesman.objects.filter(name=salesman_name).first()
        if not salesman_obj:
            raise Exception(f"Salesman Error: '{salesman_name}' is not a registered salesman.")

        # B. tbl_cmf (Main)
        cm_no = data.get('cmf_no').strip()
        if tbl_cmf.objects.filter(cm_no=cm_no).exists():
            raise Exception(f"Duplicate Error: CMF No. {cm_no} already exists in the system.")

        ct_value = data.get('colorantType')
        if ct_value == "Other": ct_value = data.get('colorantTypeOther')

        cmf_main = tbl_cmf.objects.create(
            cm_no=cm_no,
            matching_type=data.get('matchType'),
            in_code_no_id=data.get('primary_color'),
            color_desc=data.get('color_description'),
            qty_resin_testing=data.get('qty_resin_test'),
            is_resin_provided=to_bool(data.get('customerResin')),
            mi_c_resin=data.get('mi_customer_resin'),
            is_sample_available=to_bool(data.get('sampleColorant')),
            colorant_type=ct_value,
            is_guide_to_return=to_bool(data.get('color_guide_return')),
            temperature=data.get('processing_temp'),
            is_low_cost=to_bool(data.get('is_low_cost')),
            remarks=data.get('remarks'),
            user=request.user,
            sm=salesman_obj
        )

        # C. Related Tables
        c_req = data.get('colorReq')
        if c_req == "other": c_req = data.get('colorReq_other')
        tbl_cmf_color_req.objects.create(name=c_req, cm_no=cmf_main)

        tbl_cmf_dates.objects.create(
            form_made=format_date(data.get('date_created')),
            date_required=data.get('required_date'),
            date_received_lab=data.get('date_received'),
            due_date_lab=format_date(data.get('due_date')),
            cm_no=cmf_main
        )

        formula_obj = tbl_cmf_formula.objects.create(
            customer=data.get('customer'),
            finished_product=data.get('finished_product'),
            dosage=clean_numeric(data.get('dosage')),
            cm_no=cmf_main
        )

        # D. Junction Tables (Using the cleaned lists from step 1)
        for p_name in selected_processes:
            if p_name == "others": p_name = data.get('otherProcess')
            if p_name:
                p_ref, _ = tbl_cmf_process.objects.get_or_create(name=p_name.strip())
                tbl_cmf_process02.objects.create(cmf_formula_no=formula_obj, process_no=p_ref)

        for r_id in selected_resins:
            try:
                resin_ref = tbl_resin.objects.get(resin_no=r_id)
                tbl_resins_selected.objects.create(cm_no=cmf_main, resin_no=resin_ref)
            except tbl_resin.DoesNotExist:
                raise Exception(f"Resin Error: Resin ID {r_id} does not exist.")

        for s_name in selected_specs:
            if s_name == "Others": s_name = data.get('specificationOther')
            if s_name:
                s_ref, _ = tbl_cmf_specification.objects.get_or_create(name=s_name.strip())
                tbl_cmf_specification02.objects.create(cm_no=cmf_main, spec_no=s_ref)
        
        tbl_cmf_pending_completed.objects.create(cm_no=cmf_main)
        tbl_feedback_details.objects.create(cm_no=cmf_main)
        
        log_audit(request, "Saved", f"Created new CMF Entry: {cmf_main.cm_no}")
    return cmf_main

def update_cmf_complete_entry(request, original_cmf_no):
    data = request.POST

    selected_resins = [r for r in data.getlist('resin') if r.strip()]
    selected_processes = [p for p in data.getlist('process') if p.strip()]
    selected_specs = [s for s in data.getlist('specification') if s.strip()]

    if not selected_resins:
        raise Exception("Selection Required: At least one Resin Type must be selected.")
    if not selected_processes:
        raise Exception("Selection Required: At least one Process must be selected.")

    def to_bool(val):
        if val == 'Y': return True
        if val == 'N': return False
        return None

    def format_date(d_str):
        if not d_str or d_str.upper() == "ASAP": return None
        try:
            return datetime.strptime(d_str.split(',')[0].strip(), '%m/%d/%Y').strftime('%Y-%m-%d')
        except: return None

    def clean_numeric(val):
        if not val: return "0"
        return re.sub(r'[^\d.]', '', str(val))

    with transaction.atomic():
        old_cmf = tbl_cmf.objects.filter(cm_no=original_cmf_no).first()
        if not old_cmf:
            raise Exception(f"Update Failed: CMF No. {original_cmf_no} no longer exists.")

        salesman_name = data.get('salesman', '').strip()
        salesman_obj = tbl_cmf_salesman.objects.filter(name=salesman_name).first()
        if not salesman_obj:
            raise Exception(f"Salesman Error: '{salesman_name}' is not a registered salesman.")

        new_cmf_no = data.get('cmf_no').strip()
        renaming = new_cmf_no != original_cmf_no

        ct_value = data.get('colorantType')
        if ct_value == "Other": ct_value = data.get('colorantTypeOther')

        if renaming:
            if tbl_cmf.objects.filter(cm_no=new_cmf_no).exists():
                raise Exception(f"Duplicate Error: CMF No. {new_cmf_no} already belongs to another record.")

            # 1. Create the new parent row FIRST — with the updated field values —
            #    so a valid target already exists before any child row is re-pointed.
            cmf_main = tbl_cmf.objects.create(
                cm_no=new_cmf_no,
                matching_type=data.get('matchType'),
                in_code_no_id=data.get('primary_color'),
                color_desc=data.get('color_description'),
                qty_resin_testing=data.get('qty_resin_test'),
                is_resin_provided=to_bool(data.get('customerResin')),
                mi_c_resin=data.get('mi_customer_resin'),
                is_sample_available=to_bool(data.get('sampleColorant')),
                colorant_type=ct_value,
                is_guide_to_return=to_bool(data.get('color_guide_return')),
                temperature=data.get('processing_temp'),
                is_low_cost=to_bool(data.get('is_low_cost')),
                remarks=data.get('remarks'),
                user=old_cmf.user,
                sm=salesman_obj,
            )

            # 2. Re-point every dependent row from the old parent to the new one.
            #    This is the part that keeps everything connected across the rename.
            tbl_cmf_color_req.objects.filter(cm_no=old_cmf).update(cm_no=cmf_main)
            tbl_cmf_dates.objects.filter(cm_no=old_cmf).update(cm_no=cmf_main)
            tbl_cmf_formula.objects.filter(cm_no=old_cmf).update(cm_no=cmf_main)
            tbl_resins_selected.objects.filter(cm_no=old_cmf).update(cm_no=cmf_main)
            tbl_cmf_specification02.objects.filter(cm_no=old_cmf).update(cm_no=cmf_main)
            tbl_cmf_pending_completed.objects.filter(cm_no=old_cmf).update(cm_no=cmf_main)
            tbl_feedback_details.objects.filter(cm_no=old_cmf).update(cm_no=cmf_main)
            # Note: tbl_cmf_process02 links to tbl_cmf_formula (via cmf_formula_no), not
            # directly to cm_no — so it's unaffected here; it stays valid automatically
            # once tbl_cmf_formula itself is re-pointed above.

            # 3. Only now is it safe to remove the old row — nothing references it anymore.
            old_cmf.delete()
        else:
            # No rename — update the existing row in place, same as before.
            cmf_main = old_cmf
            cmf_main.matching_type = data.get('matchType')
            cmf_main.in_code_no_id = data.get('primary_color')
            cmf_main.color_desc = data.get('color_description')
            cmf_main.qty_resin_testing = data.get('qty_resin_test')
            cmf_main.is_resin_provided = to_bool(data.get('customerResin'))
            cmf_main.mi_c_resin = data.get('mi_customer_resin')
            cmf_main.is_sample_available = to_bool(data.get('sampleColorant'))
            cmf_main.colorant_type = ct_value
            cmf_main.is_guide_to_return = to_bool(data.get('color_guide_return'))
            cmf_main.temperature = data.get('processing_temp')
            cmf_main.is_low_cost = to_bool(data.get('is_low_cost'))
            cmf_main.remarks = data.get('remarks')
            cmf_main.sm = salesman_obj
            cmf_main.save()

        # From here on, cmf_main is always the correct row (renamed or not) —
        # everything below works identically in both cases.

        # B. Color Requirement
        c_req = data.get('colorReq')
        if c_req == "other": c_req = data.get('colorReq_other')
        tbl_cmf_color_req.objects.update_or_create(
            cm_no=cmf_main, defaults={'name': c_req}
        )

        # C. Dates
        tbl_cmf_dates.objects.update_or_create(
            cm_no=cmf_main,
            defaults={
                'form_made': format_date(data.get('date_created')),
                'date_required': data.get('required_date'),
                'date_received_lab': data.get('date_received'),
                'due_date_lab': format_date(data.get('due_date')),
            }
        )

        # D. Formula
        formula_obj, _ = tbl_cmf_formula.objects.update_or_create(
            cm_no=cmf_main,
            defaults={
                'customer': data.get('customer'),
                'finished_product': data.get('finished_product'),
                'dosage': clean_numeric(data.get('dosage')),
            }
        )

        # E. Junction tables — clear and recreate
        tbl_cmf_process02.objects.filter(cmf_formula_no=formula_obj).delete()
        processed_process_ids = set()
        for p_item in selected_processes:
            name = p_item.strip()
            if name.lower() == "others":
                name = data.get('otherProcess', '').strip()
            if name:
                p_ref, _ = tbl_cmf_process.objects.get_or_create(name=name)
                if p_ref.process_no not in processed_process_ids:
                    tbl_cmf_process02.objects.create(cmf_formula_no=formula_obj, process_no=p_ref)
                    processed_process_ids.add(p_ref.process_no)

        tbl_resins_selected.objects.filter(cm_no=cmf_main).delete()
        for r_id in selected_resins:
            resin_ref = tbl_resin.objects.get(resin_no=r_id)
            tbl_resins_selected.objects.create(cm_no=cmf_main, resin_no=resin_ref)

        tbl_cmf_specification02.objects.filter(cm_no=cmf_main).delete()
        processed_spec_ids = set()
        for s_item in selected_specs:
            spec_name = s_item.strip()
            if spec_name == "Others":
                spec_name = data.get('specificationOther', '').strip()
            if spec_name:
                s_ref, _ = tbl_cmf_specification.objects.get_or_create(name=spec_name)
                if s_ref.spec_no not in processed_spec_ids:
                    tbl_cmf_specification02.objects.create(cm_no=cmf_main, spec_no=s_ref)
                    processed_spec_ids.add(s_ref.spec_no)

        log_audit(
            request, "Updated",
            f"Updated CMF Entry: {original_cmf_no}" + (f" (renamed to {new_cmf_no})" if renaming else "")
        )

    return cmf_main