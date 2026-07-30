from django.db import transaction
from django.core.cache import cache
from main.services.save.utils import to_bool, format_date, clean_numeric
from main.models import (
    tbl_cmf_dates, tbl_feedback_details, tbl_cmf_color_req, tbl_cmf_pending_completed, 
    tbl_cmf_process, tbl_cmf_process02, tbl_cmf_salesman, tbl_resin, 
    tbl_resins_selected, tbl_rs, tbl_generated_prod_code
)
from main.utils.log_audit_trail import log_audit


def _get_prod_code_obj(code_str):
    """Helper to resolve the product code string into a database object."""
    if not code_str or not code_str.strip():
        return None
    # Get or create the production code record based on the string provided in the UI
    code_obj, _ = tbl_generated_prod_code.objects.get_or_create(
        product_code=code_str.strip()
    )
    return code_obj


def _extract_rs_data(request):
    data = request.POST

    colorant_type = data.get('colorantType')
    if colorant_type == "Other":
        colorant_type = data.get('colorantTypeOther')

    color_req = data.get('colorReq')
    if color_req == "other":
        color_req = data.get('colorReq_other')

    return {
        "rs_no": data.get('rs_no'),
        "customer": data.get('customer'),
        "salesman": data.get('salesman'),
        "primary_color": data.get('primary_color'),
        "quantity_required": data.get('quantity_kg'),
        "finished_product": data.get('finished_product'),
        "color_desc": data.get('color_description'),
        "date_form_made": format_date(data.get('date_created')),
        "date_lab_received": data.get('date_received'),
        "date_required": data.get('required_date'),
        "due_date": format_date(data.get('due_date')),
        "colorant_type": colorant_type,
        "color_req": color_req,
        "product_code_str": data.get('product_code'), # Raw string from UI
    }


def _save_related(request, rs_obj, data, selected_resins, selected_processes):
    for r_id in selected_resins:
        try:
            resin_ref = tbl_resin.objects.get(resin_no=r_id)
            tbl_resins_selected.objects.create(rs_no=rs_obj, resin_no=resin_ref)
        except tbl_resin.DoesNotExist:
            raise Exception(f"Resin Error: Resin ID {r_id} does not exist.")

    for p_name in selected_processes:
        if p_name == "others":
            p_name = request.POST.get('otherProcess')
        if p_name:
            p_ref, _ = tbl_cmf_process.objects.get_or_create(name=p_name.strip())
            tbl_cmf_process02.objects.create(rs_no=rs_obj, process_no=p_ref)

    if data["color_req"]:
        tbl_cmf_color_req.objects.create(name=data["color_req"], rs_no=rs_obj)


def save_rs_complete_entry(request):
    """Creates a new RS entry."""
    with transaction.atomic():
        data = _extract_rs_data(request)

        salesman_name = (data["salesman"] or "").strip()
        salesman_obj = tbl_cmf_salesman.objects.filter(name=salesman_name).first()
        if not salesman_obj:
            raise Exception(f"Salesman Error: '{salesman_name}' is not a registered salesman.")

        selected_resins = request.POST.getlist('resin')
        selected_processes = request.POST.getlist('process')

        # Resolve the string into a ForeignKey object
        code_obj = _get_prod_code_obj(data["product_code_str"])

        rs_obj = tbl_rs.objects.create(
            rs_no=data["rs_no"],
            customer=data["customer"],
            quantity_required=data["quantity_required"],
            finished_product=data["finished_product"],
            matching_type="request",
            color_desc=data["color_desc"],
            primary_color=data["primary_color"],
            colorant_type=data["colorant_type"],
            user=request.user,
            sm_no=salesman_obj,
            code_no=code_obj # Optional: if you also added this field to tbl_rs
        )
        tbl_cmf_dates.objects.create(
            rs_no=rs_obj,
            form_made=data["date_form_made"],
            date_lab_received=data["date_lab_received"], # Check field name matches: date_received_lab in model
            date_required=data["date_required"],
            due_date_lab=data["due_date"],
        )

        _save_related(request, rs_obj, data, selected_resins, selected_processes)

        # Update: Use 'code' field (FK) instead of 'prod_code' (String)
        tbl_cmf_pending_completed.objects.create(
            rs_no=rs_obj,
            code=code_obj, 
            is_completed=False
        )

        tbl_feedback_details.objects.create(rs_no=rs_obj)

        log_audit(request, "Saved", f"New RS Entry: {rs_obj.rs_no}")
        cache.delete('rs_records_list')

    return rs_obj


def update_rs_complete_entry(request, original_rs_id):
    """Updates an existing RS entry identified by primary key."""
    with transaction.atomic():
        rs_instance = tbl_rs.objects.filter(id=original_rs_id).first()
        if not rs_instance:
            raise Exception(f"RS record (id={original_rs_id}) was not found.")

        data = _extract_rs_data(request)

        salesman_name = (data["salesman"] or "").strip()
        salesman_obj = tbl_cmf_salesman.objects.filter(name=salesman_name).first()
        if not salesman_obj:
            raise Exception(f"Salesman Error: '{salesman_name}' is not a registered salesman.")

        selected_resins = request.POST.getlist('resin')
        selected_processes = request.POST.getlist('process')
        
        # Resolve the string into a ForeignKey object
        code_obj = _get_prod_code_obj(data["product_code_str"])

        rs_instance.rs_no = data["rs_no"]
        rs_instance.customer = data["customer"]
        rs_instance.quantity_required = data["quantity_required"]
        rs_instance.date_form_made = data["date_form_made"]
        rs_instance.date_lab_received = data["date_lab_received"]
        rs_instance.date_required = data["date_required"]
        rs_instance.due_date = data["due_date"]
        rs_instance.finished_product = data["finished_product"]
        rs_instance.matching_type = "request"
        rs_instance.color_desc = data["color_desc"]
        rs_instance.primary_color = data["primary_color"]
        rs_instance.colorant_type = data["colorant_type"]
        rs_instance.sm_no = salesman_obj
        rs_instance.code_no = code_obj # Update FK on main RS table if exists
        rs_instance.save()

        tbl_resins_selected.objects.filter(rs_no=rs_instance).delete()
        tbl_cmf_process02.objects.filter(rs_no=rs_instance).delete()
        tbl_cmf_color_req.objects.filter(rs_no=rs_instance).delete()
        _save_related(request, rs_instance, data, selected_resins, selected_processes)

        # Update: Use 'code' field (FK) defaults
        tbl_cmf_pending_completed.objects.update_or_create(
            rs_no=rs_instance,
            defaults={"code": code_obj}
        )

        log_audit(request, "Updated", f"RS Entry Updated: {rs_instance.rs_no} (id={rs_instance.id})")
        cache.delete('rs_records_list')

    return rs_instance


def build_form_data(rs_instance):
    # Use select_related to get the code string in one query
    pending = tbl_cmf_pending_completed.objects.filter(rs_no=rs_instance).select_related('code').first()
    color_req = tbl_cmf_color_req.objects.filter(rs_no=rs_instance).first()

    STANDARD_COLOR_REQS = {'transparent', 'opaque', 'translucent', 'metallic', 'fluorescent', 'pearlescent'}
    color_req_name = color_req.name if color_req else ''
    if color_req_name and color_req_name.lower() not in STANDARD_COLOR_REQS:
        color_req_value, color_req_other = 'other', color_req_name
    else:
        color_req_value, color_req_other = color_req_name.lower() if color_req_name else '', ''

    return {
        'original_rs_id': rs_instance.id,
        'rs_no': rs_instance.rs_no,
        'customer': rs_instance.customer,
        'salesman': rs_instance.sm_no.name if rs_instance.sm_no else '',
        'primary_color': rs_instance.primary_color,
        'quantity_kg': rs_instance.quantity_required,
        'finished_product': rs_instance.finished_product,
        'color_description': rs_instance.color_desc,
        'date_created': rs_instance.date_form_made,
        'required_date': rs_instance.date_required,
        'date_received': rs_instance.date_lab_received,
        'due_date': rs_instance.due_date,
        # Updated: Access string through the ForeignKey relation
        'product_code': pending.code.product_code if pending and pending.code else '',
        'colorantType': rs_instance.colorant_type if rs_instance.colorant_type in ('MB', 'DC') else 'Other',
        'colorantTypeOther': rs_instance.colorant_type if rs_instance.colorant_type not in ('MB', 'DC', None, '') else '',
        'colorReq': color_req_value,
        'colorReq_other': color_req_other,
        'resin': [str(x) for x in tbl_resins_selected.objects.filter(rs_no=rs_instance).values_list('resin_no__resin_no', flat=True)],
        'process': list(tbl_cmf_process02.objects.filter(rs_no=rs_instance).values_list('process_no__name', flat=True)),
    }