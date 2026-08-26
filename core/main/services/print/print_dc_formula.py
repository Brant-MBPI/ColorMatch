import os
import io
import tempfile
import threading
import uuid
import subprocess
import shutil
from decimal import Decimal

# Cross-platform Word & PDF manipulation
from docx import Document
from docx.oxml.ns import qn
import pymupdf 

from django.contrib import messages
from django.http import HttpResponse, HttpResponseServerError, JsonResponse
from django.shortcuts import redirect
from django.views.decorators.clickjacking import xframe_options_exempt

from main.utils.log_audit_trail import log_audit
from main.models import (
    tbl_dc_extruder_formula, tbl_dc_extruder_materials, tbl_dc_extruder_version,
    tbl_cmf_formula, tbl_resins_selected,
)

# Lock ensures LibreOffice instances don't collide
_word_lock = threading.Lock()

DC_TEMPLATE_PATH = os.path.join('main', 'templates', 'print_excel', 'dc_formula_template.docx')

DC_PDF_WIDTH_IN = 11.0   # Letter Width (Landscape)
DC_PDF_HEIGHT_IN = 8.5   # Letter Height (Landscape)

# Material rows: python-docx uses 0-based indexing.
# MATERIAL_START_ROW 2 (COM) -> index 1
MATERIAL_START_INDEX = 1 
MATERIAL_MAX_ROWS = 10
MAX_VERSIONS = 10
# TOTAL_ROW 12 (COM) -> index 11
TOTAL_ROW_INDEX = 11
# MATERIALS_TABLE_INDEX 2 (COM) -> index 1
MATERIALS_TABLE_INDEX = 1 

def _get_libreoffice_executable():
    """Finds the LibreOffice/soffice executable based on OS."""
    if os.name == 'nt':  # Windows
        paths = [
            r"C:\Program Files\LibreOffice\program\soffice.exe",
            r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        ]
        for path in paths:
            if os.path.exists(path): return path
        return "soffice"
    return "libreoffice"

def _resize_pdf_to_fixed_size(input_pdf_path, output_pdf_path, width_in=11.0, height_in=8.5):
    """Rescales PDF using pymupdf to exactly 11.0 x 8.5 inches."""
    target_w_pt = width_in * 72
    target_h_pt = height_in * 72
    src = pymupdf.open(input_pdf_path)
    dst = pymupdf.open()
    for page in src:
        new_page = dst.new_page(width=target_w_pt, height=target_h_pt)
        new_page.show_pdf_page(pymupdf.Rect(0, 0, target_w_pt, target_h_pt), src, page.number)
    dst.save(output_pdf_path)
    dst.close()
    src.close()

def _set_bookmark_text(doc, bookmark_name, text):
    """
    Cross-platform helper to replace text in a Word Bookmark.
    Since python-docx doesn't have a high-level bookmark API, we locate the XML tags.
    """
    text = str(text) if text is not None else ""
    # Find all bookmarkStart elements
    bookmarks_list = doc.element.xpath(f'//w:bookmarkStart[@w:name="{bookmark_name}"]')
    for bookmark in bookmarks_list:
        # Move to the parent element and find the next run or insert one
        parent = bookmark.getparent()
        # Find next sibling that is a run
        for sibling in bookmark.itersiblings():
            if sibling.tag.endswith('r'):
                # Found a run, update its text
                t = sibling.xpath('w:t')
                if t:
                    t[0].text = text
                    return
        # If no run found, append one
        new_run = parent.makeelement(qn('w:r'))
        new_text = parent.makeelement(qn('w:t'))
        new_text.text = text
        new_run.append(new_text)
        bookmark.addnext(new_run)

def _fill_and_export_dc_formula_via_word(template_abs_path, pdf_path, data):
    """Fills Docx using python-docx and converts to PDF via LibreOffice."""
    header = data['header']
    dc_materials = data['dc_materials']
    versions_by_material = data['versions_by_material']

    doc = Document(template_abs_path)

    # --- HEADER FIELDS (bookmarks) ---
    _set_bookmark_text(doc, 'code', header.code.product_code if header.code else "")
    _set_bookmark_text(doc, 'cmf', data['parent_no'])
    _set_bookmark_text(doc, 'customer', data['customer'])
    _set_bookmark_text(doc, 'resin', data['resin'])
    _set_bookmark_text(doc, 'color', data['color'])
    _set_bookmark_text(doc, 'date_matched', header.date.strftime('%m/%d/%Y') if header.date else "")
    _set_bookmark_text(doc, 'dosage', f"{_to_num(data['dosage']):.2f}%")
    _set_bookmark_text(doc, 'sample_size', header.sample_size)
    _set_bookmark_text(doc, 'mixing_time', header.mixing_time)
    _set_bookmark_text(doc, 'application', data['application'])
    _set_bookmark_text(doc, 'product_used', data['finished_product'])
    _set_bookmark_text(doc, 'note', header.notes)
    _set_bookmark_text(doc, 'matched_by', header.matched_by)
    _set_bookmark_text(doc, 'weighed_by', header.weighted_by)
    _set_bookmark_text(doc, 'encoded_by', header.encoded_by)

    # --- MATERIALS TABLE ---
    # Tables index in python-docx is 0-based
    table = doc.tables[MATERIALS_TABLE_INDEX]
    version_totals = {v: Decimal('0') for v in range(1, MAX_VERSIONS + 1)}

    for i in range(MATERIAL_MAX_ROWS):
        row_idx = MATERIAL_START_INDEX + i
        if i < len(dc_materials):
            m = dc_materials[i]
            table.cell(row_idx, 0).text = m.material or "" # Column 1 (index 0)

            v_values = versions_by_material.get(m.material_id, {})
            for v_no in range(1, MAX_VERSIONS + 1):
                col_idx = v_no # Version 1 is Column 2 (index 1)
                val = v_values.get(v_no)
                if val is not None and float(val) != 0:
                    table.cell(row_idx, col_idx).text = f"{_to_num(val):.4f}"
                    version_totals[v_no] += Decimal(str(val))
                else:
                    table.cell(row_idx, col_idx).text = ""
        else:
            table.cell(row_idx, 0).text = ""
            for v_no in range(1, MAX_VERSIONS + 1):
                table.cell(row_idx, v_no).text = ""

    # --- TOTALS ROW ---
    for v_no in range(1, MAX_VERSIONS + 1):
        col_idx = v_no
        current_total = version_totals[v_no]
        if current_total != 0:
            table.cell(TOTAL_ROW_INDEX, col_idx).text = f"{float(current_total):.4f}"
        else:
            table.cell(TOTAL_ROW_INDEX, col_idx).text = ""

    # 1. Save temp Docx
    temp_dir = os.path.dirname(pdf_path)
    temp_docx = os.path.join(temp_dir, f"temp_{uuid.uuid4().hex}.docx")
    doc.save(temp_docx)

    # 2. Convert to PDF via LibreOffice (Isolated Profile)
    profile_path = os.path.join(temp_dir, f"lo_profile_{uuid.uuid4().hex}")
    os.makedirs(profile_path, exist_ok=True)
    try:
        libreoffice_bin = _get_libreoffice_executable()
        profile_url = f"file:///{profile_path.replace(os.sep, '/')}"
        command = [
            f'"{libreoffice_bin}"', '--headless', f'"-env:UserInstallation={profile_url}"',
            '--convert-to pdf', f'--outdir "{temp_dir}"', f'"{temp_docx}"'
        ]
        subprocess.run(" ".join(command), shell=True, check=True, capture_output=True, timeout=30)
        generated_pdf = temp_docx.replace('.docx', '.pdf')
        if os.path.exists(generated_pdf):
            if os.path.exists(pdf_path): os.remove(pdf_path)
            os.rename(generated_pdf, pdf_path)
    finally:
        if os.path.exists(temp_docx): os.remove(temp_docx)
        shutil.rmtree(profile_path, ignore_errors=True)

def _fetch_dc_formula_data(formula_id):
    header = tbl_dc_extruder_formula.objects.select_related('cm_no', 'rs_no', 'code').get(pk=formula_id)
    dc_materials = list(tbl_dc_extruder_materials.objects.filter(dc=header).order_by('material_id')[:MATERIAL_MAX_ROWS])
    versions_by_material = {
        m.material_id: {v.version_no: v.value for v in m.versions.all()}
        for m in dc_materials
    }
    customer, color, resin, application, finished_product, parent_no, dosage = "", "", "", "", "", "", ""

    if header.cm_no:
        parent_no = header.cm_no.cm_no
        color = header.cm_no.color_desc
        formula_info = tbl_cmf_formula.objects.filter(cm_no=header.cm_no).first()
        if formula_info:
            customer = formula_info.customer
            application = formula_info.finished_product
            finished_product = formula_info.finished_product
            dosage = formula_info.dosage
        resin = ", ".join(tbl_resins_selected.objects.filter(cm_no=header.cm_no).values_list('resin_no__abbreviation', flat=True))
    elif header.rs_no:
        parent_no = header.rs_no.rs_no
        customer = header.rs_no.customer
        color = header.rs_no.color_desc
        application = header.rs_no.finished_product
        finished_product = header.rs_no.finished_product
        dosage = header.rs_no.dosage
        resin = ", ".join(tbl_resins_selected.objects.filter(rs_no=header.rs_no).values_list('resin_no__abbreviation', flat=True))

    return {
        'header': header, 'dc_materials': dc_materials, 'versions_by_material': versions_by_material,
        'customer': customer, 'color': color, 'dosage': dosage, 'resin': resin,
        'application': application, 'finished_product': finished_product, 'parent_no': parent_no,
    }

def _to_num(val):
    if val is None or val == "": return 0
    if isinstance(val, Decimal): return float(val)
    try: return float(val)
    except: return 0

@xframe_options_exempt
def print_dc_formula_preview(request, formula_id):
    try:
        data = _fetch_dc_formula_data(formula_id)
    except Exception as e:
        return HttpResponseServerError(f"Data Fetch Error: {str(e)}")

    template_abs_path = os.path.abspath(DC_TEMPLATE_PATH)
    with _word_lock:
        with tempfile.TemporaryDirectory() as tmpdir:
            raw_pdf_path = os.path.join(tmpdir, "raw.pdf")
            final_pdf_path = os.path.join(tmpdir, "final.pdf")
            try:
                _fill_and_export_dc_formula_via_word(template_abs_path, raw_pdf_path, data)
                _resize_pdf_to_fixed_size(raw_pdf_path, final_pdf_path, width_in=DC_PDF_WIDTH_IN, height_in=DC_PDF_HEIGHT_IN)
                with open(final_pdf_path, 'rb') as f:
                    pdf_bytes = f.read()
            except Exception as e:
                return HttpResponseServerError(f"PDF System Error: {str(e)}")

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = 'inline'
    response['X-Frame-Options'] = 'SAMEORIGIN'
    return response

def log_formula_print(request, formula_id):
    try:
        formula = tbl_dc_extruder_formula.objects.get(pk=formula_id)
        desc = f"Printed DC Formula (Code: {formula.code.product_code if formula.code else 'N/A'})"
        log_audit(request, "Printed", desc)
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)