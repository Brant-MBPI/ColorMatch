import io
from django.contrib import messages
from openpyxl import load_workbook
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from main.models import tbl_cmf, tbl_cmf_dates, tbl_cmf_formula, tbl_cmf_color_req, tbl_resins_selected, tbl_cmf_process02, tbl_cmf_specification02 # Import all relevant models

def print_cmf(request, cm_no):
    # 1. Fetch Data (Same logic as your entry view)
    try:
        # Check if the main CMF record exists
        cmf = tbl_cmf.objects.get(cm_no=cm_no)
        
    except tbl_cmf.DoesNotExist:
        messages.error(request, f"Error: CMF No. '{cm_no}' was not found in the database.")
        return redirect('cmf_entry')
    
    except Exception as e:
        messages.error(request, f"An unexpected error occurred: {str(e)}")
        return redirect('cmf_entry')
    dates = tbl_cmf_dates.objects.filter(cm_no=cmf).first()
    formula_info = tbl_cmf_formula.objects.filter(cm_no=cmf).first()
    color_req = tbl_cmf_color_req.objects.filter(cm_no=cmf).first()
    
    # Get resins string
    resins = ", ".join(list(tbl_resins_selected.objects.filter(cm_no=cmf).values_list('resin_no_id__abbreviation', flat=True)))
    
    # Get process/specs list
    process_list = list(tbl_cmf_process02.objects.filter(cmf_formula_no=formula_info).values_list('process_no__name', flat=True)) if formula_info else []
    spec_list = list(tbl_cmf_specification02.objects.filter(cm_no=cmf).values_list('spec_no__name', flat=True))

    # 2. Load Excel Template
    template_path = 'main/templates/print_excel/cmf_template.xlsx'
    wb = load_workbook(template_path)
    ws = wb.active

    # 3. Fill the Cells (Mapping based on your Excel structure)
    # General Info
    ws['E6'] = cmf.cm_no
    ws['E7'] = formula_info.customer if formula_info else ""
    ws['E8'] = dates.form_made.strftime('%m/%d/%Y') if dates and dates.form_made else ""
    ws['E9'] = dates.date_required if dates else ""
    
    # Matching Type (Checkboxes)
    ws['E11'] = "✔" if cmf.matching_type == 'new' else ""
    ws['H11'] = "✔" if cmf.matching_type == 'rematch' else ""
    
    ws['E12'] = cmf.sm.name if cmf.sm else ""
    ws['E13'] = cmf.color_desc
    ws['E14'] = formula_info.finished_product if formula_info else ""

    # Color Requirement (Logic for checkboxes)
    req_map = {'transparent': 'E17', 'opaque': 'H17', 'translucent': 'K17', 'metallic': 'E19', 'fluorescent': 'H19', 'pearlescent': 'K19'}
    if color_req and color_req.name in req_map:
        ws[req_map[color_req.name]] = "✔"
    elif color_req and color_req.name == 'other':
        ws['G21'] = cmf.color_req_other # Assuming you have this field

    # Resin and Process
    ws['C21'] = resins
    ws['E24'] = "✔" if 'injection' in process_list else ""
    ws['H24'] = "✔" if 'blow-molding' in process_list else ""
    ws['L24'] = "✔" if 'film' in process_list else ""

    ws['C35'] = formula_info.dosage if formula_info else ""
    ws['C52'] = "PRODUCT CODE: " + (getattr(cmf, 'product_code', '') or "") # Handle your product code logic here
    ws['C42'] = cmf.remarks

    # 4. Prepare Response
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    filename = f"CMF_{cm_no}.xlsx"
    response = HttpResponse(
        buffer.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename={filename}.xlsx'
    
    return response