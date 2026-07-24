import re
from django.core.cache import cache
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
        
        cache.delete('cmf_records_list')
        log_audit(request, "Saved", f"New CMF Entry: {cmf_main.cm_no}")
    return cmf_main

def update_cmf_complete_entry(request, original_cmf_no):
    data = request.POST

    # --- 1. PREPARE DATA & LISTS ---
    selected_resins = [r for r in data.getlist('resin') if r.strip()]
    selected_processes = [p for p in data.getlist('process') if p.strip()]
    selected_specs = [s for s in data.getlist('specification') if s.strip()]

    if not selected_resins:
        raise Exception("Selection Required: At least one Resin Type must be selected.")
    if not selected_processes:
        raise Exception("Selection Required: At least one Process must be selected.")

    # Helpers
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

    def get_pretty_name(field):
        mapping = {
            'matching_type': 'Matching Type', 'in_code_no_id': 'Primary Color',
            'color_desc': 'Color Description', 'qty_resin_testing': 'Qty Resin for Test',
            'is_resin_provided': 'Resin Provided', 'mi_c_resin': 'MI Customer Resin',
            'is_sample_available': 'Sample Available', 'colorant_type': 'Colorant Type',
            'is_guide_to_return': 'Guide Return', 'temperature': 'Processing Temp',
            'is_low_cost': 'Low Cost', 'remarks': 'Remarks', 'sm': 'Salesman',
            'customer': 'Customer', 'finished_product': 'Finished Product', 'dosage': 'Dosage'
        }
        return mapping.get(field, field.replace('_', ' ').title())

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

        # --- TRACKING CHANGES ---
        changed_fields = []
        selections_changed = False

        # Prepare new values for comparison
        new_values = {
            'matching_type': data.get('matchType'),
            'in_code_no_id': int(data.get('primary_color')) if data.get('primary_color') else None,
            'color_desc': data.get('color_description'),
            'qty_resin_testing': data.get('qty_resin_test'),
            'is_resin_provided': to_bool(data.get('customerResin')),
            'mi_c_resin': data.get('mi_customer_resin'),
            'is_sample_available': to_bool(data.get('sampleColorant')),
            'colorant_type': ct_value,
            'is_guide_to_return': to_bool(data.get('color_guide_return')),
            'temperature': data.get('processing_temp'),
            'is_low_cost': to_bool(data.get('is_low_cost')),
            'remarks': data.get('remarks'),
            'sm': salesman_obj
        }

        # Compare Header Fields
        for field, new_val in new_values.items():
            current_val = getattr(old_cmf, field)
            if str(current_val) != str(new_val):
                changed_fields.append(get_pretty_name(field))

        # --- EXECUTE UPDATE OR RENAME ---
        if renaming:
            if tbl_cmf.objects.filter(cm_no=new_cmf_no).exists():
                raise Exception(f"Duplicate Error: CMF No. {new_cmf_no} already exists.")

            cmf_main = tbl_cmf.objects.create(cm_no=new_cmf_no, user=old_cmf.user, **new_values)

            # Re-point dependents
            tbl_cmf_color_req.objects.filter(cm_no=old_cmf).update(cm_no=cmf_main)
            tbl_cmf_dates.objects.filter(cm_no=old_cmf).update(cm_no=cmf_main)
            tbl_cmf_formula.objects.filter(cm_no=old_cmf).update(cm_no=cmf_main)
            tbl_resins_selected.objects.filter(cm_no=old_cmf).update(cm_no=cmf_main)
            tbl_cmf_specification02.objects.filter(cm_no=old_cmf).update(cm_no=cmf_main)
            tbl_cmf_pending_completed.objects.filter(cm_no=old_cmf).update(cm_no=cmf_main)
            tbl_feedback_details.objects.filter(cm_no=old_cmf).update(cm_no=cmf_main)
            
            old_cmf.delete()
        else:
            cmf_main = old_cmf
            for field, val in new_values.items():
                setattr(cmf_main, field, val)
            cmf_main.save()

        # --- UPDATE RELATED TABLES & TRACK SUB-CHANGES ---
        # B. Color Requirement
        c_req = data.get('colorReq')
        if c_req == "other": c_req = data.get('colorReq_other')
        _, created = tbl_cmf_color_req.objects.update_or_create(cm_no=cmf_main, defaults={'name': c_req})
        if not created: selections_changed = True

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

        # D. Formula (Track sub-fields)
        formula_obj, _ = tbl_cmf_formula.objects.get_or_create(cm_no=cmf_main)
        formula_updates = {
            'customer': data.get('customer'),
            'finished_product': data.get('finished_product'),
            'dosage': clean_numeric(data.get('dosage'))
        }
        for f_field, f_val in formula_updates.items():
            if str(getattr(formula_obj, f_field)) != str(f_val):
                setattr(formula_obj, f_field, f_val)
                changed_fields.append(get_pretty_name(f_field))
        formula_obj.save()

        # E. Junction tables (Track if list changed)
        # Process JTs
        old_procs = set(tbl_cmf_process02.objects.filter(cmf_formula_no=formula_obj).values_list('process_no__name', flat=True))
        new_procs_list = []
        for p_item in selected_processes:
            p_name = data.get('otherProcess', '').strip() if p_item.lower() == "others" else p_item.strip()
            if p_name: new_procs_list.append(p_name)
        
        if old_procs != set(new_procs_list):
            selections_changed = True
            tbl_cmf_process02.objects.filter(cmf_formula_no=formula_obj).delete()
            for name in new_procs_list:
                p_ref, _ = tbl_cmf_process.objects.get_or_create(name=name)
                tbl_cmf_process02.objects.create(cmf_formula_no=formula_obj, process_no=p_ref)

        # Resin JTs
        old_resins = set(tbl_resins_selected.objects.filter(cm_no=cmf_main).values_list('resin_no_id', flat=True))
        if old_resins != set(map(int, selected_resins)):
            selections_changed = True
            tbl_resins_selected.objects.filter(cm_no=cmf_main).delete()
            for r_id in selected_resins:
                resin_ref = tbl_resin.objects.get(resin_no=r_id)
                tbl_resins_selected.objects.create(cm_no=cmf_main, resin_no=resin_ref)

        # Spec JTs
        old_specs = set(tbl_cmf_specification02.objects.filter(cm_no=cmf_main).values_list('spec_no__name', flat=True))
        new_specs_list = []
        for s_item in selected_specs:
            s_name = data.get('specificationOther', '').strip() if s_item == "Others" else s_item.strip()
            if s_name: new_specs_list.append(s_name)

        if old_specs != set(new_specs_list):
            selections_changed = True
            tbl_cmf_specification02.objects.filter(cm_no=cmf_main).delete()
            for name in new_specs_list:
                s_ref, _ = tbl_cmf_specification.objects.get_or_create(name=name)
                tbl_cmf_specification02.objects.create(cm_no=cmf_main, spec_no=s_ref)

        # --- BUILD FINAL AUDIT LOG ---
        log_msg = f"CMF: {original_cmf_no}"
        if renaming:
            log_msg += f" (Renamed to {new_cmf_no})"
        
        if not changed_fields and not selections_changed:
            log_msg += ". No data changes were made."
        else:
            if changed_fields:
                log_msg += f". Modified: {', '.join(changed_fields)}"
            if selections_changed:
                log_msg += ". Selection configurations (Resin/Process/Specification) were updated."
        cache.delete('cmf_records_list')
        log_audit(request, "Updated", log_msg)

    return cmf_main