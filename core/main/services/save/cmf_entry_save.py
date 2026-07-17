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
            primary_color=data.get('primary_color'),
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