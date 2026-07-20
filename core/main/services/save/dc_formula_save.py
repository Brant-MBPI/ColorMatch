from django.db import transaction
from ...models import (
    tbl_cmf, tbl_generated_prod_code,
    tbl_dc_extruder_formula, tbl_dc_extruder_formula02
)

def save_dc_complete_formula(request):
    post_data = request.POST
    
    with transaction.atomic():
        # 1. Resolve Foreign Keys
        prod_code_str = post_data.get('product_code')
        prod_code_obj = tbl_generated_prod_code.objects.filter(prod_code=prod_code_str).first()
        
        cm_no_val = post_data.get('cmf_number')
        cmf_obj = tbl_cmf.objects.get(cm_no=cm_no_val)

        # 2. Create the Header (tbl_dc_extruder_formula)
        header = tbl_dc_extruder_formula.objects.create(
            date=post_data.get('date_matched') or None,
            cm_no=cmf_obj,
            code=prod_code_obj,
            sample_size=post_data.get('sample_size'),
            mixing_time=post_data.get('mixing_time'),
            matched_by=post_data.get('matched_by'),
            weighted_by=post_data.get('weighed_by'),
            encoded_by=post_data.get('encoded_by'),
            total_weight=post_data.get('total_weight') or 0,
            L=post_data.get('spectro_l') or 0,
            A=post_data.get('spectro_a') or 0,
            B=post_data.get('spectro_b') or 0,
            C=post_data.get('spectro_c') or 0,
            H=post_data.get('spectro_h') or 0,
            html=post_data.get('srgb_hex'),
            c=post_data.get('cmyk_c') or 0,
            m=post_data.get('cmyk_m') or 0,
            y=post_data.get('cmyk_y') or 0,
            k=post_data.get('cmyk_k') or 0,
        )

        # 3. Create the Ingredients (tbl_dc_extruder_formula02)
        for i in range(1, 11):
            mat_name = post_data.get(f'material_{i}')
            if mat_name and mat_name.strip():
                tbl_dc_extruder_formula02.objects.create(
                    dc=header,
                    material=mat_name,
                    value=post_data.get(f'percentage_{i}') or 0,
                    weight=post_data.get(f'weight_{i}') or 0
                )
        
        return header