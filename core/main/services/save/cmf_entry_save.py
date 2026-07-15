from datetime import datetime
from ...models import tbl_cmf_entry

def handle_cmf_entry_save(request):
    """
    Service to process POST data and save a CMF Entry.
    """
    data = request.POST

    # --- 1. Helper for Date Conversion ---
    def parse_dt(date_str):
        if not date_str: return None
        try:
            return datetime.strptime(date_str, '%m/%d/%Y').strftime('%Y-%m-%d')
        except ValueError:
            return date_str

    # --- 2. Process Complex Fields (Others, Checkboxes) ---
    
    # Color Requirement
    color_req = data.get('colorReq')
    if color_req == "other":
        color_req = data.get('colorReq_other')

    # Processes
    processes = data.getlist('process')
    if "others" in processes:
        processes.remove("others")
        other_p = data.get('otherProcess')
        if other_p: processes.append(other_p)
    process_string = ", ".join(processes)

    # Colorant Type
    colorant_type = data.get('colorantType')
    if colorant_type == "Other":
        colorant_type = data.get('colorantTypeOther')

    # Specifications
    specs = data.getlist('specification')
    if "Others" in specs:
        specs.remove("Others")
        other_s = data.get('specificationOther')
        if other_s: specs.append(other_s)
    specs_string = ", ".join(specs)

    # --- 3. Create the Database Record ---
    new_entry = tbl_cmf_entry.objects.create(
        cmf_no=data.get('cmf_no'),
        customer=data.get('customer'),
        date_created=parse_dt(data.get('date_created')),
        required_date=data.get('required_date'),
        date_received=data.get('date_received'),
        due_date=parse_dt(data.get('due_date')),
        match_type=data.get('matchType'),
        salesman=data.get('salesman'),
        finished_product=data.get('finished_product'),
        primary_color_id=data.get('primary_color'),
        description=data.get('color_description'),
        color_requirement=color_req,
        process=process_string,
        qty_resin_test=data.get('qty_resin_test'),
        customer_resin_provided=data.get('customerResin'),
        mi_customer_resin=data.get('mi_customer_resin'),
        sample_colorant_available=data.get('sampleColorant'),
        colorant_type=colorant_type,
        dosage=data.get('dosage'),
        processing_temp=data.get('processing_temp'),
        other_specifications=specs_string,
        color_guide_return=data.get('color_guide_return'),
        is_low_cost=data.get('is_low_cost'),
        remarks=data.get('remarks'),
        product_code=data.get('product_code'),
        created_by=request.user
    )

    # --- 4. Handle Many-to-Many ---
    selected_resins = data.getlist('resin')
    if selected_resins:
        new_entry.resins.set(selected_resins)

    return new_entry