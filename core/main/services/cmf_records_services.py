from django.db import transaction
from datetime import datetime
from .models import (
    tbl_cmf, tbl_cmf_color_req, tbl_cmf_dates, tbl_cmf_formula, 
    tbl_cmf_process, tbl_cmf_process02, tbl_resin, tbl_resins_selected,
    tbl_cmf_specification, tbl_cmf_specification02, tbl_cmf_salesman
)

def save_cmf_complete_entry(request):
    data = request.POST
    
    # --- 1. STRICT VALIDATION ---
    # List of all required keys from your HTML names
    required_fields = [
        'cmf_no', 'customer', 'date_created', 'required_date', 'date_received', 
        'due_date', 'matchType', 'salesman', 'finished_product', 'primary_color', 
        'color_description', 'colorReq', 'qty_resin_test', 'customerResin', 
        'mi_customer_resin', 'sampleColorant', 'colorantType', 'dosage', 
        'processing_temp', 'color_guide_return', 'is_low_cost'
    ]
    
    for field in required_fields:
        if not data.get(field):
            raise Exception(f"The field '{field.replace('_', ' ').title()}' is required and cannot be empty.")

    # Check for many-to-many lists
    if not data.getlist('resin'): raise Exception("At least one Resin Type must be selected.")
    if not data.getlist('process'): raise Exception("At least one Process must be selected.")
    if not data.getlist('specification'): raise Exception("At least one Specification must be selected.")

    # --- 2. HELPERS ---
    def format_date(d_str):
        try:
            return datetime.strptime(d_str.split(',')[0].strip(), '%m/%d/%Y').strftime('%Y-%m-%d')
        except: return None

    def clean_num(val):
        return ''.join(filter(lambda x: x.isdigit() or x == '.', str(val)))

    # --- 3. DATABASE TRANSACTION ---
    with transaction.atomic():
        # A. Lookup Salesman
        salesman_obj = tbl_cmf_salesman.objects.filter(name=data.get('salesman')).first()
        if not salesman_obj:
            raise Exception("Selected salesman not found in database.")

        # B. tbl_cmf (Main)
        cm_no = data.get('cmf_no')
        if tbl_cmf.objects.filter(cm_no=cm_no).exists():
            raise Exception(f"CMF Number {cm_no} already exists.")

        colorant_type = data.get('colorantType')
        if colorant_type == "Other": colorant_type = data.get('colorantTypeOther')

        cmf_main = tbl_cmf.objects.create(
            cm_no=cm_no,
            matching_type=data.get('matchType'),
            primary_color_id=data.get('primary_color'),
            color_description=data.get('color_description'),
            qty_resin_testing=data.get('qty_resin_test'),
            is_resin_provided=data.get('customerResin'),
            mi_c_resin=data.get('mi_customer_resin'),
            is_sample_available=data.get('sampleColorant'),
            colorant_type=colorant_type,
            is_guide_to_return=data.get('color_guide_return'),
            temperature=data.get('processing_temp'),
            is_low_cost=data.get('is_low_cost'),
            remarks=data.get('remarks'),
            user=request.user,
            sm_no=salesman_obj
        )

        # C. tbl_cmf_color_req
        c_req = data.get('colorReq')
        if c_req == "other": c_req = data.get('colorReq_other')
        tbl_cmf_color_req.objects.create(name=c_req, cm_no=cm_no)

        # D. tbl_cmf_dates
        tbl_cmf_dates.objects.create(
            form_made=format_date(data.get('date_created')),
            date_required=data.get('required_date'),
            date_received_lab=data.get('date_received'),
            due_date_lab=format_date(data.get('due_date'))
        )

        # E. tbl_cmf_formula
        formula_obj = tbl_cmf_formula.objects.create(
            customer=data.get('customer'),
            finished_product=data.get('finished_product'),
            dosage=clean_num(data.get('dosage')),
            cm_no=cm_no
        )

        # F. tbl_cmf_process02
        for p_name in data.getlist('process'):
            if p_name == "others": p_name = data.get('otherProcess')
            p_ref, _ = tbl_cmf_process.objects.get_or_create(name=p_name)
            tbl_cmf_process02.objects.create(cmf_formula_no=formula_obj, process_no=p_ref)

        # G. tbl_resins_selected
        for r_id in data.getlist('resin'):
            r_ref = tbl_resin.objects.get(resin_no=r_id)
            tbl_resins_selected.objects.create(cm_no=cm_no, resin_no=r_ref)

        # H. tbl_cmf_specification02
        for s_name in data.getlist('specification'):
            if s_name == "Others": s_name = data.get('specificationOther')
            s_ref, _ = tbl_cmf_specification.objects.get_or_create(name=s_name)
            tbl_cmf_specification02.objects.create(cm_no=cm_no, spec_no=s_ref)

    return cmf_main