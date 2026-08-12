import os
import tempfile
import threading
import uuid

import pythoncom
import win32com.client as win32
from django.contrib import messages
from django.http import HttpResponse, HttpResponseServerError
from django.shortcuts import redirect
from django.views.decorators.clickjacking import xframe_options_exempt

from main.models import (
    tbl_cmf, tbl_cmf_dates, tbl_cmf_formula, tbl_cmf_color_req,
    tbl_resins_selected, tbl_cmf_process02, tbl_cmf_specification02,
    tbl_mb_extruder_formula, tbl_dc_extruder_formula
)

# Excel COM automation isn't safe to run from multiple threads/requests at
# once. Serialize access so only one conversion happens at a time.
_excel_lock = threading.Lock()

TEMPLATE_PATH = os.path.join('main', 'templates', 'print_excel', 'cmf_template.xlsx')


def _fetch_cmf_data(cm_no):
    """Pulls everything needed from the DB. Raises tbl_cmf.DoesNotExist if not found."""
    cmf = tbl_cmf.objects.get(cm_no=cm_no)
    dates = tbl_cmf_dates.objects.filter(cm_no=cmf).first()
    formula_info = tbl_cmf_formula.objects.filter(cm_no=cmf).first()
    color_req_obj = tbl_cmf_color_req.objects.filter(cm_no=cmf).first()

    resins = ", ".join(list(tbl_resins_selected.objects.filter(cm_no=cmf).values_list('resin_no__abbreviation', flat=True)))
    process_list = list(tbl_cmf_process02.objects.filter(cmf_formula_no=formula_info).values_list('process_no__name', flat=True)) if formula_info else []
    spec_list = list(tbl_cmf_specification02.objects.filter(cm_no=cmf).values_list('spec_no__name', flat=True))

    final_prod_code = ""
    final_f = tbl_mb_extruder_formula.objects.filter(cm_no=cmf, is_final=True).select_related('code').first()
    if not final_f:
        final_f = tbl_dc_extruder_formula.objects.filter(cm_no=cmf, is_final=True).select_related('code').first()
    if final_f and final_f.code:
        final_prod_code = final_f.code.product_code

    return {
        'cmf': cmf,
        'dates': dates,
        'formula_info': formula_info,
        'color_req_obj': color_req_obj,
        'resins': resins,
        'process_list': process_list,
        'spec_list': spec_list,
        'final_prod_code': final_prod_code,
    }


def _fill_and_export_via_excel(template_abs_path, pdf_path, data):
    """
    Opens the ORIGINAL template directly in Excel (no openpyxl involved,
    so drawings/form controls/checkboxes/images are untouched), writes
    values into cells via COM, exports to PDF, then closes WITHOUT
    saving — the template file on disk is never modified.
    """
    cmf = data['cmf']
    dates = data['dates']
    formula_info = data['formula_info']
    color_req_obj = data['color_req_obj']
    resins = data['resins']
    process_list = data['process_list']
    spec_list = data['spec_list']
    final_prod_code = data['final_prod_code']

    pythoncom.CoInitialize()
    excel = None
    wb = None
    try:
        excel = win32.DispatchEx("Excel.Application")
        excel.Visible = False
        excel.DisplayAlerts = False

        wb = excel.Workbooks.Open(template_abs_path)
        ws = wb.Worksheets(1)

        def set_cell(addr, value):
            ws.Range(addr).Value = value

        # --- GENERAL INFORMATION ---
        set_cell('F6', cmf.cm_no)
        set_cell('F7', formula_info.customer if formula_info else "")
        set_cell('F8', dates.form_made.strftime('%m/%d/%Y') if dates and dates.form_made else "")
        set_cell('F9', dates.date_required if dates else "")
        set_cell('F11', cmf.matching_type == 'new')        # linked checkbox
        set_cell('I11', cmf.matching_type == 'rematch')    # linked checkbox
        set_cell('F12', cmf.sm.name if cmf.sm else "")
        set_cell('F13', cmf.color_desc)
        set_cell('F14', formula_info.finished_product if formula_info else "")

        # --- COLOR REQUIREMENT ---
        c_req_name = color_req_obj.name if color_req_obj else ""
        standard_reqs = ['transparent', 'opaque', 'translucent', 'metallic', 'fluorescent', 'pearlescent']
        req_map = {'transparent': 'F17', 'opaque': 'I17', 'translucent': 'L17', 'metallic': 'F19', 'fluorescent': 'I19', 'pearlescent': 'L19'}

        # Uncheck all, then check the matching one
        for addr in req_map.values():
            set_cell(addr, False)
        set_cell('F21', False)

        if c_req_name in standard_reqs:
            set_cell(req_map[c_req_name], True)
        elif c_req_name:
            set_cell('F21', True)          # "Others" checkbox
            set_cell('H21', c_req_name)    # "Others" text

        # --- RESIN & PROCESS ---
        set_cell('F22', resins)
        set_cell('F24', 'injection' in process_list)
        set_cell('I24', 'blow-molding' in process_list)
        set_cell('M24', 'film' in process_list)
        set_cell('F26', 'pipe-extrusion' in process_list)

        standard_procs = ['injection', 'blow-molding', 'film', 'pipe-extrusion']
        other_procs = [p for p in process_list if p not in standard_procs]
        set_cell('I26', bool(other_procs))
        set_cell('L26', ", ".join(other_procs) if other_procs else "")

        # --- TECHNICAL SPECS ---
        set_cell('F28', cmf.qty_resin_testing)
        set_cell('F29', cmf.is_resin_provided is True)
        set_cell('I29', cmf.is_resin_provided is False)
        set_cell('F30', cmf.mi_c_resin)

        set_cell('F31', cmf.is_sample_available is True)
        set_cell('I31', cmf.is_sample_available is False)

        # Colorant Type
        set_cell('F33', cmf.colorant_type == 'MB')
        set_cell('I33', cmf.colorant_type == 'DC')
        is_other_colorant = cmf.colorant_type not in ('MB', 'DC')
        set_cell('L33', is_other_colorant)
        set_cell('O33', cmf.colorant_type if is_other_colorant else "")

        set_cell('F35', formula_info.dosage if formula_info else "")
        set_cell('F37', cmf.is_guide_to_return is True)
        set_cell('I37', cmf.is_guide_to_return is False)

        # Specifications
        set_cell('F39', 'Food Contact' in spec_list)
        set_cell('I39', 'Sunlight Exposure' in spec_list)

        standard_specs = ['Food Contact', 'Sunlight Exposure']
        other_specs = [s for s in spec_list if s not in standard_specs]
        set_cell('F41', bool(other_specs))
        set_cell('G41', ", ".join(other_specs) if other_specs else "")

        set_cell('F43', cmf.temperature)
        set_cell('F44', cmf.is_low_cost is True)
        set_cell('I44', cmf.is_low_cost is False)

        # --- REMARKS & PRODUCT CODE ---
        set_cell('C48', cmf.remarks)
        set_cell('D62', final_prod_code)

        # 0 = xlTypePDF
        ws.ExportAsFixedFormat(0, pdf_path)

    finally:
        if wb is not None:
            wb.Close(SaveChanges=False)   # never overwrite the template
        if excel is not None:
            excel.Quit()
        pythoncom.CoUninitialize()


def print_cmf_preview(request, cm_no):
    """
    Fills the ORIGINAL Excel template directly via COM (preserving all
    drawings/checkboxes/formatting), exports to PDF for inline browser
    preview, and cleans up the temp PDF before returning.
    """
    try:
        data = _fetch_cmf_data(cm_no)
    except tbl_cmf.DoesNotExist:
        messages.error(request, f"Error: CMF No. '{cm_no}' was not found.")
        return redirect('cmf_entry')
    except Exception as e:
        messages.error(request, f"System Error: {str(e)}")
        return redirect('cmf_entry')

    template_abs_path = os.path.abspath(TEMPLATE_PATH)
    if not os.path.exists(template_abs_path):
        return HttpResponseServerError("Template file not found on server.")

    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_path = os.path.join(tmpdir, f"{uuid.uuid4().hex}.pdf")

        try:
            with _excel_lock:
                _fill_and_export_via_excel(template_abs_path, pdf_path, data)
        except Exception as e:
            return HttpResponseServerError(f"PDF export failed: {str(e)}")

        if not os.path.exists(pdf_path):
            return HttpResponseServerError("PDF export failed: no output file produced.")

        with open(pdf_path, 'rb') as f:
            pdf_bytes = f.read()
    # TemporaryDirectory context manager deletes the pdf here, unconditionally.

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = 'inline'
    response['X-Frame-Options'] = 'SAMEORIGIN'
    return response


print_cmf_preview = xframe_options_exempt(print_cmf_preview)