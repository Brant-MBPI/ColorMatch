from django.db import transaction
from django.core.cache import cache

from core.main.models import tbl_cmf_pending_completed, tbl_rs
from core.main.utils.log_audit_trail import log_audit

# from .models import tbl_rs, tbl_cmf_pending_completed
# from .audit import log_audit


def _extract_rs_data(request):
    """Pulls and normalizes RS form fields from the POST payload."""
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
        "color_description": data.get('color_description'),
        "date_form_made": data.get('date_created'),
        "date_lab_received": data.get('date_received'),
        "date_required": data.get('required_date'),
        "due_date": data.get('due_date'),
        "product_code": data.get('product_code'),
        "colorant_type": colorant_type,
        "color_req": color_req,
    }


def save_rs_complete_entry(request):
    """Creates a new RS entry. Raises Exception on duplicate rs_no."""
    with transaction.atomic():
        data = _extract_rs_data(request)
        rs_no_val = data["rs_no"]

        if tbl_rs.objects.filter(rs_no=rs_no_val).exists():
            raise Exception(f"Duplicate Error: RS No. {rs_no_val} already exists in the system.")

        rs_obj = tbl_rs.objects.create(
            rs_no=rs_no_val,
            customer=data["customer"],
            quantity_required=data["quantity_required"],
            date_form_made=data["date_form_made"],
            date_lab_received=data["date_lab_received"],
            date_required=data["date_required"],
            due_date=data["due_date"],
            finished_product=data["finished_product"],
            color_description=data["color_description"],
            primary_color=data["primary_color"],
            colorant_type=data["colorant_type"],
            status="Pending"
        )

        tbl_cmf_pending_completed.objects.create(
            rs_no=rs_obj,
            prod_code=data["product_code"],
            is_completed=False
        )

        log_audit(request, "Saved", f"New RS Entry: {rs_obj.rs_no}")
        cache.delete('rs_records_list')

    return rs_obj


def update_rs_complete_entry(request, original_rs_no):
    """Updates an existing RS entry identified by original_rs_no.
    Raises Exception if not found, or if renamed into a rs_no that already exists."""
    with transaction.atomic():
        rs_instance = tbl_rs.objects.filter(rs_no=original_rs_no).first()
        if not rs_instance:
            raise Exception(f"RS No. {original_rs_no} was not found.")

        data = _extract_rs_data(request)
        rs_no_val = data["rs_no"]

        if rs_no_val != original_rs_no and tbl_rs.objects.filter(rs_no=rs_no_val).exists():
            raise Exception(f"Duplicate Error: RS No. {rs_no_val} already exists in the system.")

        rs_instance.rs_no = rs_no_val
        rs_instance.customer = data["customer"]
        rs_instance.quantity_required = data["quantity_required"]
        rs_instance.date_form_made = data["date_form_made"]
        rs_instance.date_lab_received = data["date_lab_received"]
        rs_instance.date_required = data["date_required"]
        rs_instance.due_date = data["due_date"]
        rs_instance.finished_product = data["finished_product"]
        rs_instance.color_description = data["color_description"]
        rs_instance.primary_color = data["primary_color"]
        rs_instance.colorant_type = data["colorant_type"]
        rs_instance.save()

        tbl_cmf_pending_completed.objects.update_or_create(
            rs_no=rs_instance,
            defaults={"prod_code": data["product_code"]}
        )

        log_audit(request, "Updated", f"RS Entry Updated: {rs_instance.rs_no}")
        cache.delete('rs_records_list')

    return rs_instance