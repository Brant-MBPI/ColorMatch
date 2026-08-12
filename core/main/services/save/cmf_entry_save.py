import io
from django.contrib import messages
from openpyxl import load_workbook
from django.http import HttpResponse
from django.shortcuts import redirect
from main.models import (
    tbl_cmf, tbl_cmf_dates, tbl_cmf_formula, tbl_cmf_color_req, 
    tbl_resins_selected, tbl_cmf_process02, tbl_cmf_specification02,
    tbl_mb_extruder_formula, tbl_dc_extruder_formula
)

def print_cmf(request, cm_no):
    try:
        # 1. Fetch Main Data
        cmf = tbl_cmf.objects.get(cm_no=cm_no)
        dates = tbl_cmf_dates.objects.filter(cm_no=cmf).first()
        formula_info = tbl_cmf_formula.objects.filter(cm_no=cmf).first()
        color_req_obj = tbl_cmf_color_req.objects.filter(cm_no=cmf).first()
        
        # 2. Fetch Junction Data
        resins = ", ".join(list(tbl_resins_selected.objects.filter(cm_no=cmf).values_list('resin_no__abbreviation', flat=True)))
        process_list = list(tbl_cmf_process02.objects.filter(cmf_formula_no=formula_info).values_list('process_no__name', flat=True)) if formula_info else []
        spec_list = list(tbl_cmf_specification02.objects.filter(cm_no=cmf).values_list('spec_no__name', flat=True))

        # 3. Get Final Product Code (Check MB then DC tables)
        final_prod_code = ""
        final_f = tbl_mb_extruder_formula.objects.filter(cm_no=cmf, is_final=True).select_related('code').first()
        if not final_f:
            final_f = tbl_dc_extruder_formula.objects.filter(cm_no=cmf, is_final=True).select_related('code').first()
        if final_f and final_f.code:
            final_prod_code = final_f.code.product_code

    except tbl_cmf.DoesNotExist:
        messages.error(request, f"Error: CMF No. '{cm_no}' was not found.")
        return redirect('cmf_entry')
    except Exception as e:
        messages.error(request, f"System Error: {str(e)}")
        return redirect('cmf_entry')

    # 4. Load Excel Template
    template_path = 'main/templates/print_excel/cmf_template.xlsx'
    wb = load_workbook(template_path)
    ws = wb.active

    # --- GENERAL INFORMATION ---
    ws['F6'] = cmf.cm_no
    ws['F7'] = formula_info.customer if formula_info else ""
    ws['F8'] = dates.form_made.strftime('%m/%d/%Y') if dates and dates.form_made else ""
    ws['F9'] = dates.date_required if dates else ""
    ws['F11'] = "✔" if cmf.matching_type == 'new' else ""
    ws['I11'] = "✔" if cmf.matching_type == 'rematch' else ""
    ws['F12'] = cmf.sm.name if cmf.sm else ""
    ws['F13'] = cmf.color_desc
    ws['F14'] = formula_info.finished_product if formula_info else ""

    # --- COLOR REQUIREMENT ---
    c_req_name = color_req_obj.name if color_req_obj else ""
    standard_reqs = ['transparent', 'opaque', 'translucent', 'metallic', 'fluorescent', 'pearlescent']
    req_map = {'transparent': 'F17', 'opaque': 'I17', 'translucent': 'L17', 'metallic': 'F19', 'fluorescent': 'I19', 'pearlescent': 'L19'}

    if c_req_name in standard_reqs:
        ws[req_map[c_req_name]] = "✔"
    elif c_req_name:
        ws['F21'] = "✔" # Others checkbox
        ws['H21'] = c_req_name # Others text

    # --- RESIN & PROCESS ---
    ws['D21'] = resins
    ws['F24'] = "✔" if 'injection' in process_list else ""
    ws['I24'] = "✔" if 'blow-molding' in process_list else ""
    ws['M24'] = "✔" if 'film' in process_list else ""
    ws['F26'] = "✔" if 'pipe-extrusion' in process_list else ""
    
    # Process Others logic
    standard_procs = ['injection', 'blow-molding', 'film', 'pipe-extrusion']
    other_procs = [p for p in process_list if p not in standard_procs]
    if other_procs:
        ws['I26'] = "✔"
        ws['L26'] = ", ".join(other_procs)

    # --- TECHNICAL SPECS ---
    ws['F28'] = cmf.qty_resin_testing
    ws['F29'] = "✔" if cmf.is_resin_provided is True else ""
    ws['I29'] = "✔" if cmf.is_resin_provided is False else ""
    ws['F30'] = cmf.mi_c_resin
    
    ws['F31'] = "✔" if cmf.is_sample_available is True else ""
    ws['I31'] = "✔" if cmf.is_sample_available is False else ""

    # Colorant Type
    if cmf.colorant_type == 'MB': ws['F33'] = "✔"
    elif cmf.colorant_type == 'DC': ws['I33'] = "✔"
    else:
        ws['L33'] = "✔"
        ws['O33'] = cmf.colorant_type

    ws['F35'] = formula_info.dosage if formula_info else ""
    ws['F37'] = "✔" if cmf.is_guide_to_return is True else ""
    ws['I37'] = "✔" if cmf.is_guide_to_return is False else ""

    # Specifications
    ws['F39'] = "✔" if 'Food Contact' in spec_list else ""
    ws['I39'] = "✔" if 'Sunlight Exposure' in spec_list else ""

    standard_specs = ['Food Contact', 'Sunlight Exposure']
    other_specs = [s for s in spec_list if s not in standard_specs]
    if other_specs:
        ws['F41'] = "✔"
        ws['G41'] = ", ".join(other_specs)

    ws['F43'] = cmf.temperature
    ws['F44'] = "✔" if cmf.is_low_cost is True else ""
    ws['I44'] = "✔" if cmf.is_low_cost is False else ""

    # --- REMARKS & PRODUCT CODE ---
    ws['C48'] = cmf.remarks
    ws['D62'] = final_prod_code

    # 5. Prepare File Response
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    response = HttpResponse(
        buffer.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    # Double check extension isn't doubled
    response['Content-Disposition'] = f'inline; filename=CMF_{cm_no}.xlsx'
    
    return response