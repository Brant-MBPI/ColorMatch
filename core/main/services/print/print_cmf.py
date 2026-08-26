import os
import tempfile
import threading
import uuid

import pythoncom
import win32com.client as win32
from django.contrib import messages
from django.http import HttpResponse, HttpResponseServerError, JsonResponse
from django.shortcuts import redirect
from django.views.decorators.clickjacking import xframe_options_exempt

from main.utils.log_audit_trail import log_audit
from main.services.print.print_util import _resize_pdf_to_fixed_size
from main.models import (
    tbl_cmf, tbl_cmf_dates, tbl_cmf_formula, tbl_cmf_color_req,
    tbl_resins_selected, tbl_cmf_process02, tbl_cmf_specification02,
    tbl_mb_extruder_formula, tbl_dc_extruder_formula
)

# Excel COM automation isn't safe to run from multiple threads/requests at
# once. Serialize access so only one conversion happens at a time.
_excel_lock = threading.Lock()

TEMPLATE_PATH = os.path.join('main', 'templates', 'print_excel', 'new_cmf_template.xlsx')


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
    Fills the Excel template using COM automation with specific coordinates 
    and '/' character for checkboxes.
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

        # Helper for checkbox behavior: returns '/' if condition is true, else empty string
        check = lambda condition: '/' if condition else ''

        # --- GENERAL INFORMATION ---
        set_cell('F7', cmf.cm_no)
        set_cell('F9', formula_info.customer if formula_info else "")
        set_cell('F11', dates.form_made.strftime('%m/%d/%Y') if dates and dates.form_made else "")
        set_cell('F13', dates.date_required if dates else "")
        set_cell('F15', cmf.sm.name if cmf.sm else "")
        
        # Matching Type (Row 16)
        set_cell('F17', check(cmf.matching_type == 'new'))
        set_cell('I17', check(cmf.matching_type == 'rematch'))
        
        # Product Status (Row 18)
        set_cell('F19', check(cmf.product_status == 'existing'))
        set_cell('L19', check(cmf.product_status == 'new'))
        
        set_cell('F21', formula_info.finished_product if formula_info else "")
        set_cell('F23', cmf.color_desc)

        # --- COLOR REQUIREMENT ---
        c_req_name = color_req_obj.name if color_req_obj else ""
        standard_reqs = ['transparent', 'opaque', 'translucent', 'metallic', 'fluorescent', 'pearlescent']
        req_map = {
            'transparent': 'F25', 'opaque': 'I25', 'translucent': 'L25', 
            'metallic': 'F27', 'fluorescent': 'I27', 'pearlescent': 'L27'
        }

        # Clear standard req cells and 'Others' checkbox
        for addr in req_map.values(): set_cell(addr, "")
        set_cell('F29', "")
        set_cell('H29', "")

        if c_req_name in standard_reqs:
            set_cell(req_map[c_req_name], "/")
        elif c_req_name:
            set_cell('F29', "/")           # "Others" checkbox
            set_cell('H29', c_req_name)    # "Others" text value

        # --- SAMPLE COLORANT AVAILABLE ---
        set_cell('F31', check(cmf.is_sample_available is True))
        set_cell('I31', check(cmf.is_sample_available is False))

        # --- TYPE OF COLORANT ---
        set_cell('F33', check(cmf.colorant_type == 'MB'))
        set_cell('I33', check(cmf.colorant_type == 'DC'))
        is_other_colorant = cmf.colorant_type not in ('MB', 'DC')
        set_cell('L33', check(is_other_colorant))
        set_cell('O33', cmf.colorant_type if is_other_colorant else "")

        # --- DOSAGE, QTY ORDER, RESIN ---
        set_cell('F35', formula_info.dosage if formula_info else "")
        ws.Range('F37').NumberFormat = "#,##0.00 \"KG\""
        set_cell('F37', cmf.est_qty_order) # New Field
        set_cell('F39', resins)

        # --- PROCESS ---
        set_cell('F41', check('injection' in process_list))
        set_cell('I41', check('blow-molding' in process_list))
        set_cell('L41', check('film' in process_list))
        set_cell('F43', check('pipe-extrusion' in process_list))
        
        standard_procs = ['injection', 'blow-molding', 'film', 'pipe-extrusion']
        other_procs = [p for p in process_list if p not in standard_procs]
        set_cell('I43', check(bool(other_procs))) # Others checkbox
        set_cell('K43', ", ".join(other_procs) if other_procs else "") # Others value

        # --- RESIN PROVIDED & MI ---
        set_cell('F45', cmf.qty_resin_testing)
        set_cell('F47', check(cmf.is_resin_provided is True))
        set_cell('I47', check(cmf.is_resin_provided is False))
        set_cell('F49', cmf.mi_c_resin)

        # --- COLOR GUIDE RETURN ---
        set_cell('F51', check(cmf.is_guide_to_return is True))
        set_cell('I51', check(cmf.is_guide_to_return is False))

        # --- OTHER SPECIFICATIONS ---
        set_cell('F53', check('Food Contact' in spec_list))
        set_cell('I53', check('Sunlight Exposure' in spec_list))
        
        standard_specs = ['Food Contact', 'Sunlight Exposure']
        other_specs = [s for s in spec_list if s not in standard_specs]
        set_cell('F55', check(bool(other_specs))) # Others checkbox
        set_cell('H55', ", ".join(other_specs) if other_specs else "") # Others value

        # --- TEMPERATURE & LOW COST ---
        set_cell('F57', cmf.temperature)
        set_cell('F59', check(cmf.is_low_cost is True))
        set_cell('I59', check(cmf.is_low_cost is False))

        # --- REMARKS & PRODUCT CODE ---
        set_cell('C64', cmf.remarks)
        set_cell('D76', final_prod_code)

        # --- PAGE SETUP ---
        ps = ws.PageSetup
        ps.LeftMargin = 0
        ps.RightMargin = 0
        ps.TopMargin = 0
        ps.BottomMargin = 0
        ps.HeaderMargin = 0
        ps.FooterMargin = 0
        ps.Zoom = False
        ps.FitToPagesWide = 1
        ps.FitToPagesTall = 1

        # Export to PDF (xlTypePDF = 0)
        ws.ExportAsFixedFormat(0, pdf_path)

    finally:
        if wb is not None:
            wb.Close(SaveChanges=False)
        if excel is not None:
            excel.Quit()
        pythoncom.CoUninitialize()


def print_cmf_preview(request, cm_no):
    """
    Fills the ORIGINAL Excel template directly via COM (preserving all
    drawings/checkboxes/formatting), exports to PDF, resizes that PDF to
    a fixed 8.5in x 6.5in page with no margin, and serves it inline for
    browser preview. All temp files are cleaned up before returning.
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
        raw_pdf_path = os.path.join(tmpdir, f"{uuid.uuid4().hex}_raw.pdf")
        final_pdf_path = os.path.join(tmpdir, f"{uuid.uuid4().hex}_final.pdf")

        try:
            with _excel_lock:
                _fill_and_export_via_excel(template_abs_path, raw_pdf_path, data)
            _resize_pdf_to_fixed_size(
                raw_pdf_path, final_pdf_path,
                width_in=6.5, height_in=8.5,
            )
        except Exception as e:
            return HttpResponseServerError(f"PDF export failed: {str(e)}")

        import fitz as _fitz_debug
        _doc = _fitz_debug.open(final_pdf_path)
        print("FINAL PDF PAGE SIZE (pt):", _doc[0].rect)
        _doc.close()
        if not os.path.exists(final_pdf_path):
            return HttpResponseServerError("PDF export failed: no output file produced.")

        with open(final_pdf_path, 'rb') as f:
            pdf_bytes = f.read()
    # TemporaryDirectory context manager deletes both PDFs here, unconditionally.

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = 'inline'
    response['X-Frame-Options'] = 'SAMEORIGIN'
    return response


print_cmf_preview = xframe_options_exempt(print_cmf_preview)



def log_cmf_print(request, cm_no):
    try:
        # Record the action in the audit trail
        log_audit(request, "Printed", f"Printed Color Matching Form (CMF No: {cm_no})")
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    



