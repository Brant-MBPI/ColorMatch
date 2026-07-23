from datetime import datetime
from django.db import IntegrityError, transaction
from main.utils.log_audit_trail import log_audit
from ...models import (
    tbl_cmf, tbl_generated_prod_code,
    tbl_mb_extruder_formula, tbl_mb_extruder_formula02
)

def save_mb_complete_formula(request):
    post_data = request.POST
    formula_id = post_data.get('formula_id') # Hidden field from template
    
    # Helper to handle empty numeric strings or spaces
    def clean_num(val):
        if val is None: return None
        v = str(val).strip()
        return v if v else None

    # Helper to format field names for the Audit Trail
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
            # 1. Resolve Product Code (Get or Create)
            prod_code_str = post_data.get('product', '').strip()
            prod_code_obj = None
            if prod_code_str:
                prod_code_obj, _ = tbl_generated_prod_code.objects.get_or_create(
                    product_code=prod_code_str
                )
            
            # 2. Resolve CMF Foreign Key
            cm_no_val = post_data.get('cm_form_no')
            cmf_obj = tbl_cmf.objects.get(cm_no=cm_no_val)

            # 3. Standardize Date
            raw_date = post_data.get('date')
            formatted_date = None
            if raw_date:
                try:
                    formatted_date = datetime.strptime(raw_date, '%m/%d/%Y').date()
                except ValueError:
                    formatted_date = raw_date

            # 4. Prepare Header Data Dictionary
            header_data = {
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

            if formula_id:
                # --- UPDATE LOGIC ---
                header = tbl_mb_extruder_formula.objects.get(pk=formula_id)
                
                # Check for changes in header
                for field, new_value in header_data.items():
                    current_value = getattr(header, field)
                    # Convert both to string to avoid Decimal/Float/None comparison issues
                    if str(current_value) != str(new_value):
                        setattr(header, field, new_value)
                        changed_fields.append(get_pretty_name(field))
                
                header.save()
                
                # Update Ingredients (Clear and Re-save)
                tbl_mb_extruder_formula02.objects.filter(mb=header).delete()
                action_type = "Updated"
            else:
                # --- CREATE LOGIC ---
                header = tbl_mb_extruder_formula.objects.create(**header_data)
                action_type = "Saved"

            # 5. Save/Re-save Ingredients (1-10 rows)
            ingredients_added = False
            for i in range(1, 11):
                mat_name = post_data.get(f'material_{i}')
                if mat_name and mat_name.strip():
                    tbl_mb_extruder_formula02.objects.create(
                        mb=header,
                        material=mat_name,
                        value=clean_num(post_data.get(f'percentage_{i}')) or 0,
                        weight=clean_num(post_data.get(f'weight_{i}')) or 0
                    )
                    ingredients_added = True

            # 6. Construct Detailed Audit Trail Message
            lot_display = header.lot_no if header.lot_no else "N/A"
            
            if action_type == "Updated":
                msg = f"Updated MB Formula (Lot: {lot_display}). "
                if changed_fields:
                    msg += f"Modified fields: {', '.join(changed_fields)}. "
                if ingredients_added:
                    msg += "Material composition updated."
            else:
                msg = f"Saved new MB Formula (Lot: {lot_display}) for CMF: {cmf_obj.cm_no}."

            log_audit(request, action_type, msg)
            
            return header

    except IntegrityError:
        raise Exception("The Lot Number provided already exists in the system. Please use a unique Lot Number.")
    except Exception as e:
        raise Exception(f"Database Error: {str(e)}")