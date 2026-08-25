import re
from django.http import JsonResponse
from django.db.models import Max
from main.models import (
    tbl_cmf, tbl_cmf_formula, tbl_resins_selected, 
    tbl_cmf_process02, tbl_master_formula, tbl_generated_prod_code
)

def get_formulation_details(request):
    cm_no = request.GET.get('cm_no')
    cmf = tbl_cmf.objects.filter(cm_no=cm_no).first()
    
    if not cmf:
        return JsonResponse({'error': 'Not found'}, status=404)

    # 1. Identify Colorant Type
    colorant_type = (cmf.colorant_type or "").upper()
    
    formula_info = tbl_cmf_formula.objects.filter(cm_no=cm_no).first()
    
    # Concatenate Resins
    resins = tbl_resins_selected.objects.filter(cm_no=cmf).values_list('resin_no__abbreviation', flat=True)
    resin_str = ", ".join(filter(None, resins))

    # Concatenate Processes
    processes = tbl_cmf_process02.objects.filter(cmf_formula_no=formula_info).values_list('process_no__name', flat=True)
    app_str = ", ".join(filter(None, processes))

    # 2. Product Code Generation Logic
    generated_code = ""
    
    if colorant_type == 'MB':
        # Get the prefix letter (e.g., 'G')
        prefix = cmf.in_code_no.code if cmf.in_code_no else ""
        
        if prefix:
            # We look for the pattern: Prefix + Fixed (A) + 5 Digits + Fixed (E)
            # Adjust the 'A' and 'E' if your fixed characters are different
            # Regex: ^[Prefix]A(\d{5})E$
            pattern = rf'^{prefix}A(\d{{5}})E$'
            
            # Helper function to find the max number in a specific table
            def get_max_from_table(model, field_name, search_prefix, regex_pattern):
                codes = model.objects.filter(**{f"{field_name}__startswith": search_prefix}).values_list(field_name, flat=True)
                nums = []
                for c in codes:
                    match = re.match(regex_pattern, str(c))
                    if match:
                        nums.append(int(match.group(1)))
                return max(nums) if nums else 0

            # Get max from Master Formula
            max_mf = get_max_from_table(tbl_master_formula, 'product_code', prefix, pattern)
            
            # Get max from Generated Prod Code
            max_gen = get_max_from_table(tbl_generated_prod_code, 'product_code', prefix, pattern)
            
            # Determine the final latest number and increment
            latest_num = max(max_mf, max_gen)
            new_num = latest_num + 1
            
            # Format back to string: Prefix + A + 5-digit zero-padded number + E
            # Example: G + A + 32213 + E = GA32213E
            generated_code = f"{prefix}A{str(new_num).zfill(5)}E"
    
    elif colorant_type == 'DC':
        # Placeholder for DC logic
        generated_code = "DC_LOGIC_PENDING"

    data = {
        'customer': formula_info.customer if formula_info else "",
        'resin': resin_str,
        'color': cmf.in_code_no.color if cmf.in_code_no else (cmf.color_desc or ""),
        'product_code': generated_code if generated_code else (cmf.in_code_no.code if cmf.in_code_no else ""),
        'dosage': formula_info.dosage if formula_info else "",
        'application': app_str,
        'finished_product': formula_info.finished_product if formula_info else "",
        'colorant_type': colorant_type,
    }
    return JsonResponse(data)