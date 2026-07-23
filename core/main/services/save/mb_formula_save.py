from datetime import datetime
from decimal import Decimal
from django.db import IntegrityError, transaction
from main.utils.log_audit_trail import log_audit
from ...models import (
    tbl_cmf, tbl_generated_prod_code,
    tbl_mb_extruder_formula, tbl_mb_extruder_formula02
)

def save_mb_complete_formula(request):
    post_data = request.POST
    formula_id = post_data.get('formula_id')
    
    def clean_num(val):
        if val is None: return None
        v = str(val).strip()
        return v if v else None

    def get_pretty_name(field):
        mapping = {
            'lot_no': 'Lot Number', 'mixing_time': 'Mixing Time',
            'matched_by': 'Matched By', 'weighted_by': 'Weighed By',
            'encoded_by': 'Encoded By', 'total_weight': 'Total Weight',
            'html': 'sRGB Hex', 'L': 'Spectro L', 'A': 'Spectro A',
            'B': 'Spectro B', 'C': 'Spectro C', 'H': 'Spectro H'
        }
        return mapping.get(field, field.replace('_', ' ').title())

    try:
        with transaction.atomic():
            # 1. Resolve Product Code
            prod_code_str = post_data.get('product', '').strip()
            prod_code_obj, _ = tbl_generated_prod_code.objects.get_or_create(product_code=prod_code_str) if prod_code_str else (None, False)
            
            # 2. Resolve CMF
            cmf_obj = tbl_cmf.objects.get(cm_no=post_data.get('cm_form_no'))

            # 3. Standardize Date
            raw_date = post_data.get('date')
            formatted_date = datetime.strptime(raw_date, '%m/%d/%Y').date() if raw_date else None

            # 4. Prepare Header Data
            header_params = {
                'date': formatted_date,
                'cm_no': cmf_obj,
                'code': prod_code_obj,
                'lot_no': post_data.get('lot_number'),
                'mixing_time': post_data.get('mixing_time'),
                'matched_by': post_data.get('matched_by'),
                'weighted_by': post_data.get('weighed_by'),
                'encoded_by': post_data.get('encoded_by'),
                'total_weight': clean_num(post_data.get('total_weight')) or 0,
                'L': clean_num(post_data.get('spectro_l')),
                'A': clean_num(post_data.get('spectro_a')),
                'B': clean_num(post_data.get('spectro_b')),
                'C': clean_num(post_data.get('spectro_c')),
                'H': clean_num(post_data.get('spectro_h')),
                'html': post_data.get('srgb_hex'),
                'c': clean_num(post_data.get('cmyk_c')),
                'm': clean_num(post_data.get('cmyk_m')),
                'y': clean_num(post_data.get('cmyk_y')),
                'k': clean_num(post_data.get('cmyk_k')),
            }

            changed_fields = []
            ingredients_changed = False

            if formula_id:
                header = tbl_mb_extruder_formula.objects.get(pk=formula_id)
                
                # --- TRACK HEADER CHANGES ---
                for field, new_value in header_params.items():
                    current_value = getattr(header, field)
                    if str(current_value) != str(new_value):
                        setattr(header, field, new_value)
                        changed_fields.append(get_pretty_name(field))
                header.save()

                # --- TRACK INGREDIENT CHANGES ---
                # 1. Get existing ingredients from DB
                old_ings = list(tbl_mb_extruder_formula02.objects.filter(mb=header).values('material', 'value', 'weight'))
                
                # 2. Construct the new list from POST data
                new_ings = []
                for i in range(1, 11):
                    mat = post_data.get(f'material_{i}', '').strip()
                    if mat:
                        new_ings.append({
                            'material': mat,
                            'value': Decimal(clean_num(post_data.get(f'percentage_{i}')) or 0),
                            'weight': Decimal(clean_num(post_data.get(f'weight_{i}')) or 0)
                        })

                # 3. Compare lists
                if str(old_ings) != str(new_ings):
                    ingredients_changed = True
                    # If changed, delete and recreate
                    tbl_mb_extruder_formula02.objects.filter(mb=header).delete()
                    for ing in new_ings:
                        tbl_mb_extruder_formula02.objects.create(mb=header, **ing)
                
                action_type = "Updated"
            else:
                # --- CREATE LOGIC ---
                header = tbl_mb_extruder_formula.objects.create(**header_params)
                for i in range(1, 11):
                    mat = post_data.get(f'material_{i}', '').strip()
                    if mat:
                        tbl_mb_extruder_formula02.objects.create(
                            mb=header,
                            material=mat,
                            value=clean_num(post_data.get(f'percentage_{i}')) or 0,
                            weight=clean_num(post_data.get(f'weight_{i}')) or 0
                        )
                action_type = "Saved"

            # 5. Build Audit Message
            lot_display = header.lot_no if header.lot_no else "N/A"
            if action_type == "Updated":
                if not changed_fields and not ingredients_changed:
                    msg = f"Viewed/Saved MB Formula (Lot: {lot_display}) without changes."
                else:
                    msg = f"Updated MB Formula (Lot: {lot_display}). "
                    if changed_fields: msg += f"Modified: {', '.join(changed_fields)}. "
                    if ingredients_changed: msg += "Material composition updated."
            else:
                msg = f"Saved new MB Formula (Lot: {lot_display}) for CMF: {cmf_obj.cm_no}."

            log_audit(request, action_type, msg)
            return header

    except IntegrityError:
        raise Exception("The Lot Number provided already exists.")
    except Exception as e:
        raise Exception(f"Database Error: {str(e)}")