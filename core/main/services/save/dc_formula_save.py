from decimal import Decimal
from datetime import datetime
from django.db import IntegrityError, transaction
from main.utils.log_audit_trail import log_audit
from ...models import (
    tbl_cmf, tbl_generated_prod_code,
    tbl_dc_extruder_formula, tbl_dc_extruder_formula02
)

def save_dc_complete_formula(request):
    post_data = request.POST
    formula_id = post_data.get('formula_id') # Hidden field in DC form
    
    # Helper to handle empty numeric strings or spaces
    def clean_num(val):
        if val is None: return None
        v = str(val).strip()
        return v if v else None

    # Helper to format field names for the Audit Trail
    def get_pretty_name(field):
        mapping = {
            'lot_no': 'Lot Number', 'sample_size': 'Sample Size',
            'mixing_time': 'Mixing Time', 'matched_by': 'Matched By',
            'weighted_by': 'Weighed By', 'encoded_by': 'Encoded By',
            'total_weight': 'Total Weight', 'html': 'sRGB Hex',
            'L': 'Spectro L', 'A': 'Spectro A', 'B': 'Spectro B',
            'C': 'Spectro C', 'H': 'Spectro H'
        }
        return mapping.get(field, field.replace('_', ' ').title())

    try:
        with transaction.atomic():
            # 1. Resolve Product Code (Get or Create)
            prod_code_str = post_data.get('product_code', '').strip()
            prod_code_obj = None
            if prod_code_str:
                prod_code_obj, _ = tbl_generated_prod_code.objects.get_or_create(
                    product_code=prod_code_str
                )
            
            # 2. Resolve CMF Foreign Key
            cm_no_val = post_data.get('cmf_number')
            cmf_obj = tbl_cmf.objects.get(cm_no=cm_no_val)

            # 3. Standardize Date (MM/DD/YYYY -> YYYY-MM-DD)
            raw_date = post_data.get('date_matched')
            formatted_date = None
            if raw_date:
                try:
                    formatted_date = datetime.strptime(raw_date, '%m/%d/%Y').date()
                except ValueError:
                    formatted_date = raw_date

            # 4. Prepare Header Data Dictionary
            header_params = {
                'date': formatted_date,
                'cm_no': cmf_obj,
                'code': prod_code_obj,
                'lot_no': post_data.get('lot_number'),
                'sample_size': post_data.get('sample_size'),
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
                # --- UPDATE LOGIC ---
                header = tbl_dc_extruder_formula.objects.get(pk=formula_id)
                
                # Check for changes in header
                for field, new_value in header_params.items():
                    current_value = getattr(header, field)
                    if str(current_value) != str(new_value):
                        setattr(header, field, new_value)
                        changed_fields.append(get_pretty_name(field))
                
                header.save()

                # --- TRACK INGREDIENT CHANGES ---
                # 1. Get existing ingredients from DB
                old_ings = list(tbl_dc_extruder_formula02.objects.filter(dc=header).values('material', 'value', 'weight'))
                
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

                # 3. Compare and conditionally update
                if str(old_ings) != str(new_ings):
                    ingredients_changed = True
                    tbl_dc_extruder_formula02.objects.filter(dc=header).delete()
                    for ing in new_ings:
                        tbl_dc_extruder_formula02.objects.create(dc=header, **ing)
                
                action_type = "Updated"
            else:
                # --- CREATE LOGIC ---
                header = tbl_dc_extruder_formula.objects.create(**header_params)
                for i in range(1, 11):
                    mat = post_data.get(f'material_{i}', '').strip()
                    if mat:
                        tbl_dc_extruder_formula02.objects.create(
                            dc=header,
                            material=mat,
                            value=clean_num(post_data.get(f'percentage_{i}')) or 0,
                            weight=clean_num(post_data.get(f'weight_{i}')) or 0
                        )
                action_type = "Saved"

            # 5. Build Audit Message
            lot_display = header.lot_no if header.lot_no else "N/A"
            p_code = prod_code_obj.product_code if prod_code_obj else "N/A"

            if action_type == "Updated":
                if not changed_fields and not ingredients_changed:
                    msg = f"Viewed/Saved DC Formula (Lot: {lot_display}) without changes."
                else:
                    msg = f"Updated DC Formula (Lot: {lot_display}). "
                    if changed_fields: msg += f"Modified: {', '.join(changed_fields)}. "
                    if ingredients_changed: msg += "Material composition updated."
            else:
                msg = f"Saved new DC Formula (Lot: {lot_display}) with Product Code: {p_code} for CMF: {cmf_obj.cm_no}."

            log_audit(request, action_type, msg)
            
            return header

    except IntegrityError:
        raise Exception("The Lot Number provided already exists. Please use a unique Lot Number.")
    except Exception as e:
        raise Exception(f"Database Error: {str(e)}")