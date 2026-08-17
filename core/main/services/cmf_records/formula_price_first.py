import io
import os
import threading
import re
import json
import win32com.client as win32
import tempfile
import uuid
import pythoncom
from django.db.models import Max
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from main.services.cmf_records import cmf_records_services # or local check
from main.models import tbl_cmf, tbl_cmf_formula, tbl_dc_extruder_formula, tbl_dc_extruder_materials, tbl_dc_extruder_version, tbl_mb_extruder_formula, tbl_mb_extruder_formula02, tbl_resins_selected

def get_price_first_data(request):
    # Expects a list of objects: [{"id": 1, "type": "MB"}, ...]
    import json
    selected_items = json.loads(request.GET.get('items', '[]'))
    
    results = []
    
    for item in selected_items:
        f_id = item['id']
        f_type = item['type']
        
        # 1. Get Header and Ingredients
        if f_type == 'MB':
            header = tbl_mb_extruder_formula.objects.select_related('code', 'cm_no', 'rs_no').get(pk=f_id)
            ingredients = tbl_mb_extruder_formula02.objects.filter(mb=header).order_by('id')
        else:
            header = tbl_dc_extruder_formula.objects.select_related('code', 'cm_no', 'rs_no').get(pk=f_id)
            ingredients = tbl_dc_extruder_formula02.objects.filter(dc=header).order_by('id')

        # 2. Extract Parent Data (CMF/RS)
        parent = header.cm_no or header.rs_no
        customer = ""
        dosage = ""
        end_product = ""
        salesman = ""
        matching_type = ""
        
        if header.cm_no:
            formula_info = tbl_cmf_formula.objects.filter(cm_no=header.cm_no).first()
            customer = formula_info.customer if formula_info else ""
            dosage = formula_info.dosage if formula_info else ""
            end_product = formula_info.finished_product if formula_info else ""
            salesman = header.cm_no.sm.name if header.cm_no.sm else ""
            matching_type = header.cm_no.matching_type
        elif header.rs_no:
            customer = header.rs_no.customer
            dosage = header.rs_no.dosage
            end_product = header.rs_no.finished_product
            salesman = "" # Adjust based on your RS model
            matching_type = header.rs_no.matching_type

        # 3. Format Resins ("A, B, and C")
        resins_list = list(tbl_resins_selected.objects.filter(
            cm_no=header.cm_no if header.cm_no else None,
            rs_no=header.rs_no if header.rs_no else None
        ).values_list('resin_no__abbreviation', flat=True))
        
        if len(resins_list) == 0:
            resin_str = ""
        elif len(resins_list) == 1:
            resin_str = resins_list[0]
        else:
            resin_str = ", ".join(resins_list[:-1]) + " and " + resins_list[-1]

        # 4. "Others" (Matching Logic)
        others_val = "new matching"
        if matching_type == 'rematch' and header.cm_no:
            curr_cm = header.cm_no.cm_no # e.g. A9128b
            # Split: find the trailing letters
            match = re.match(r"([A-Z0-9]+)([a-z]+)", curr_cm)
            if match:
                base_code = match.group(1) # A9128
                # Find the latest CMF with this base code excluding current
                prev_cmf = tbl_cmf.objects.filter(cm_no__startswith=base_code).exclude(cm_no=curr_cm).order_by('-cm_no').first()
                if prev_cmf:
                    # Find product code for that CMF
                    
                    prev_pc = "Unknown"
                    # Check MB table first
                    pc_check = tbl_mb_extruder_formula.objects.filter(cm_no=prev_cmf, is_final=True).select_related('code').first()
                    if not pc_check:
                        pc_check = tbl_dc_extruder_formula.objects.filter(cm_no=prev_cmf, is_final=True).select_related('code').first()
                    
                    if pc_check and pc_check.code:
                        prev_pc = pc_check.code.product_code
                    
                    others_val = f"rematch of {prev_pc}"
        elif matching_type == 'request':
            others_val = "request"

        # 5. Build row for each ingredient
        total_conc = sum([float(i.value or 0) for i in ingredients])
        
        for ing in ingredients:
            results.append({
                'date': header.date.strftime('%B %d, %Y') if header.date else "",
                'customer': customer,
                'classification': f_type.lower(),
                'prod_code': header.code.product_code if header.code else "",
                'resin': resin_str,
                'mat_code': ing.material,
                'mat_conc': f"{float(ing.value or 0):.6f}",
                'end_product': end_product,
                'total': f"{total_conc:.2f}",
                'others': others_val,
                'dosage': f"{float(dosage or 0):.2f}",
                'salesman': salesman,
                'cmf_no': header.cm_no.cm_no if header.cm_no else (header.rs_no.rs_no if header.rs_no else "none"),
                'html': (header.html or "").replace('#', ''),
                'c': int(header.c or 0),
                'm': int(header.m or 0),
                'y': int(header.y or 0),
                'k': int(header.k or 0),
            })

    return JsonResponse({'data': results})


# Same reasoning as the Excel print exports — one COM instance at a time.
_excel_lock = threading.Lock()

FORMULA_TEMPLATE_PATH = os.path.join('main', 'templates', 'print_excel', 'Formula.xlsx')
FORMULA_TEMPLATE_PASSWORD = "maranatha101"

# Matches the "Formula" sheet's header row (A1:S1) exactly, in column order.
COLUMN_ORDER = [
    'date', 'customer', 'classification', 'prod_code', 'resin', 'mat_code',
    'mat_conc', 'end_product', 'total', 'others', 'dosage', 'salesman_name',
    'cmf_no', 'html', 'c', 'm', 'y', 'k', 'remarks'
]

DATA_START_ROW = 2  # row 1 is the header


def _fill_formula_sheet_via_excel(template_abs_path, output_path, rows):
    """
    Opens the password-protected template directly in Excel via COM,
    writes the Price First rows into the 'Formula' sheet (3rd tab)
    starting at row 2, autofits columns, then saves a NEW file at
    output_path — protected with the same password. Password args are
    passed POSITIONALLY, not as keyword args — with late-bound COM
    dispatch (DispatchEx), keyword arguments can silently fail to map
    to the correct parameter, which caused Excel to open with no
    password at all and pop its own blocking password dialog.
    """
    pythoncom.CoInitialize()
    excel = None
    wb = None
    try:
        excel = win32.DispatchEx("Excel.Application")
        excel.Visible = False
        excel.DisplayAlerts = False

        # Workbooks.Open positional signature:
        # (FileName, UpdateLinks, ReadOnly, Format, Password, ...)
        wb = excel.Workbooks.Open(
            template_abs_path,  # FileName
            0,                  # UpdateLinks
            False,              # ReadOnly
            None,               # Format
            FORMULA_TEMPLATE_PASSWORD,  # Password
        )
        ws = wb.Worksheets("Formula")

        for r_idx, row in enumerate(rows):
            excel_row = DATA_START_ROW + r_idx
            for c_idx, field in enumerate(COLUMN_ORDER):
                col_letter = chr(ord('A') + c_idx)
                ws.Range(f"{col_letter}{excel_row}").Value = row.get(field, "")

        ws.Columns.AutoFit()

        # SaveAs positional signature: (Filename, FileFormat, Password, ...)
        wb.SaveAs(
            output_path,                 # Filename
            51,                          # FileFormat: xlOpenXMLWorkbook (.xlsx)
            FORMULA_TEMPLATE_PASSWORD,   # Password
        )

    finally:
        if wb is not None:
            wb.Close(SaveChanges=False)
        if excel is not None:
            excel.Quit()
        pythoncom.CoUninitialize()


def download_price_first_excel(request):
    """
    Fills the 'Formula' sheet of the protected Formula.xlsx template
    with the Price First modal's current rows (including user-typed
    Remarks), autofits columns, and returns the result as a download.
    The original template is opened read-only (via COM, password
    supplied) and never modified.
    """
    if request.method != 'POST':
        return HttpResponseBadRequest("POST required.")

    try:
        payload = json.loads(request.body)
        rows = payload.get('rows', [])
    except (json.JSONDecodeError, TypeError):
        return HttpResponseBadRequest("Invalid JSON body.")

    if not rows:
        return HttpResponseBadRequest("No rows to export.")

    # The frontend sends rows as flat arrays (one value per column, same
    # order as COLUMN_ORDER) — convert each to a dict keyed by field name
    # so _fill_formula_sheet_via_excel can look values up by field.
    row_dicts = []
    for row in rows:
        row_dicts.append({field: (row[i] if i < len(row) else "") for i, field in enumerate(COLUMN_ORDER)})

    template_abs_path = os.path.abspath(FORMULA_TEMPLATE_PATH)
    if not os.path.exists(template_abs_path):
        return HttpResponseBadRequest("Formula.xlsx template not found on server.")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, f"{uuid.uuid4().hex}.xlsx")

        try:
            with _excel_lock:
                _fill_formula_sheet_via_excel(template_abs_path, output_path, row_dicts)
        except Exception as e:
            return HttpResponseBadRequest(f"Excel export failed: {str(e)}")

        if not os.path.exists(output_path):
            return HttpResponseBadRequest("Excel export failed: no output file produced.")

        with open(output_path, 'rb') as f:
            file_bytes = f.read()

    response = HttpResponse(
        file_bytes,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="Formula.xlsx"'
    return response