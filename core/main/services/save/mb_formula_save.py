from datetime import datetime
from django.db import transaction
from main.utils.log_audit_trail import log_audit
from ...models import (
    tbl_cmf, tbl_generated_prod_code,
    tbl_mb_extruder_formula, tbl_mb_extruder_formula02
)

def save_mb_complete_formula(request):
    post_data = request.POST
    
    with transaction.atomic():
        # 1. Resolve Foreign Keys
        prod_code_str = post_data.get('product')
        prod_code_obj = None
        if prod_code_str:
            prod_code_obj, _ = tbl_generated_prod_code.objects.get_or_create(
                product_code=prod_code_str.strip()
            )
        
        cm_no_val = post_data.get('cm_form_no')
        cmf_obj = tbl_cmf.objects.get(cm_no=cm_no_val)

        # --- DATE FORMATTING FIX ---
        raw_date = post_data.get('date')
        formatted_date = None
        if raw_date:
            try:
                # Convert MM/DD/YYYY string to Python Date Object
                formatted_date = datetime.strptime(raw_date, '%m/%d/%Y').date()
            except ValueError:
                # Fallback if date is already in YYYY-MM-DD or other format
                formatted_date = raw_date

        # Helper to handle empty numeric strings
        def clean_num(val):
            return val if (val and val.strip()) else None

        # 2. Create the Header
        header = tbl_mb_extruder_formula.objects.create(
            date=formatted_date, # Use the formatted date here
            cm_no=cmf_obj,
            code=prod_code_obj,
            lot_no=post_data.get('lot_number'),
            mixing_time=post_data.get('mixing_time'),
            matched_by=post_data.get('matched_by'),
            weighted_by=post_data.get('weighted_by'),
            encoded_by=post_data.get('encoded_by'),
            total_weight=clean_num(post_data.get('total_weight')) or 0,
            L=clean_num(post_data.get('spectro_l')),
            A=clean_num(post_data.get('spectro_a')),
            B=clean_num(post_data.get('spectro_b')),
            C=clean_num(post_data.get('spectro_c')),
            H=clean_num(post_data.get('spectro_h')),
            html=post_data.get('srgb_hex'),
            c=clean_num(post_data.get('cmyk_c')),
            m=clean_num(post_data.get('cmyk_m')),
            y=clean_num(post_data.get('cmyk_y')),
            k=clean_num(post_data.get('cmyk_k')),
        )

        # 3. Create the Ingredients
        for i in range(1, 11):
            mat_name = post_data.get(f'material_{i}')
            if mat_name and mat_name.strip():
                tbl_mb_extruder_formula02.objects.create(
                    mb=header,
                    material=mat_name,
                    value=clean_num(post_data.get(f'percentage_{i}')) or 0,
                    weight=clean_num(post_data.get(f'weight_{i}')) or 0
                )
                
        # Safe logging even if prod_code_obj is None
        p_code = prod_code_obj.product_code if prod_code_obj else "N/A"
        lot_no = header.lot_no if header.lot_no else "N/A"
        log_audit(request, "Saved", f"Created new MB Formula with Lot Number: {lot_no} and Product Code: {p_code}")
        
        return header