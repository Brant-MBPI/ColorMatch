import os
import io
import tempfile
import threading
import uuid
import subprocess
import shutil
from decimal import Decimal

# Cross-platform Word Templating & PDF manipulation
from docxtpl import DocxTemplate
import pymupdf 

from django.contrib import messages
from django.http import HttpResponse, HttpResponseServerError, JsonResponse
from django.shortcuts import redirect
from django.views.decorators.clickjacking import xframe_options_exempt

from main.utils.log_audit_trail import log_audit
from main.models import (
    tbl_cmf_process02, tbl_dc_extruder_formula, tbl_dc_extruder_materials, tbl_dc_extruder_version,
    tbl_cmf_formula, tbl_resins_selected,
)

# Lock ensures LibreOffice instances don't collide
_word_lock = threading.Lock()

TEMPLATE_PATH = os.path.join('main', 'templates', 'print_excel', 'dc_formula_template.docx')

# Landscape Letter Dimensions
DC_PDF_WIDTH_IN = 11.0   
DC_PDF_HEIGHT_IN = 8.5   

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
    return "libreoffice" # Linux/Synology

def _resize_pdf_to_fixed_size(input_pdf_path, output_pdf_path, width_in=11.0, height_in=8.5):
    """
    Rescales every page using pymupdf to exactly 11.0 x 8.5 inches.
    Only takes the FIRST PAGE (index 0) to prevent layout overflows.
    """
    target_w_pt = width_in * 72
    target_h_pt = height_in * 72

    src = pymupdf.open(input_pdf_path)
    dst = pymupdf.open()

    if len(src) > 0:
        new_page = dst.new_page(width=target_w_pt, height=target_h_pt)
        # Force the first page content into the landscape rectangle
        new_page.show_pdf_page(
            pymupdf.Rect(0, 0, target_w_pt, target_h_pt),
            src,
            0,
        )

    dst.save(output_pdf_path)
    dst.close()
    src.close()

def _clean(val):
    """Strips newlines and extra spaces that break Word alignment."""
    if val is None: return ""
    return str(val).replace('\r', '').replace('\n', ' ').strip()

def _fill_and_export_dc_formula_via_word(template_abs_path, pdf_path, data):
    """Fills the docx template using docxtpl and converts to PDF."""
    header = data['header']
    dc_materials = data['dc_materials']
    versions_by_material = data['versions_by_material']

    # 1. Load the Template via docxtpl (Safe for layout)
    doc = DocxTemplate(template_abs_path)

    # 2. Build Context (Exactly matching your {{tags}} in the image)
    context = {
        'code': _clean(header.code.product_code if header.code else ""),
        'cmf': _clean(data['parent_no']),
        'customer': _clean(data['customer']),
        'resin': _clean(data['resin']),
        'color': _clean(data['color']),
        'date_matched': header.date.strftime('%m/%d/%Y') if header.date else "",
        'dosage': f"{float(data.get('dosage') or 0):.2f}%",
        'sample_size': _clean(header.sample_size),
        'mixing_time': _clean(header.mixing_time),
        'application': _clean(data['application']),
        'product_used': _clean(data['finished_product']),
        'note': _clean(header.notes),
        'matched_by': _clean(header.matched_by),
        'weighed_by': _clean(header.weighted_by),
        'encoded_by': _clean(header.encoded_by),
    }

    # 3. Fill Table (m0 thru m9 and v1 thru v10)
    version_totals = [Decimal('0')] * 10

    for i in range(10): # Match tags {{m0n}} to {{m9n}}
        m_name_key = f'm{i}n'
        if i < len(dc_materials):
            mat_obj = dc_materials[i]
            context[m_name_key] = _clean(mat_obj.material)
            
            v_values = versions_by_material.get(mat_obj.material_id, {})
            for v_no in range(1, 11): # Match tags {{m0v1}} to {{m0v10}}
                val = v_values.get(v_no)
                val_key = f'm{i}v{v_no}'
                if val is not None and float(val) != 0:
                    context[val_key] = f"{float(val):.4f}"
                    version_totals[v_no-1] += Decimal(str(val))
                else:
                    context[val_key] = ""
        else:
            context[m_name_key] = ""
            for v_no in range(1, 11): context[f'm{i}v{v_no}'] = ""

    # 4. Fill Totals (tv1 thru tv10)
    for idx, total in enumerate(version_totals):
        v_num = idx + 1
        context[f'tv{v_num}'] = f"{float(total):.4f}" if total > 0 else ""

    # 5. Render (Execute the swap)
    doc.render(context)

    # 6. Save temp Docx
    temp_dir = os.path.dirname(pdf_path)
    temp_docx = os.path.join(temp_dir, f"temp_{uuid.uuid4().hex}.docx")
    doc.save(temp_docx)

    # 7. PDF Conversion with Isolated Profile (Fixes Refused Connection)
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
    """Pulls everything needed from the DB."""
    header = tbl_dc_extruder_formula.objects.select_related('cm_no', 'rs_no', 'code').get(pk=formula_id)
    dc_materials = list(tbl_dc_extruder_materials.objects.filter(dc=header).order_by('material_id')[:10])
    versions_by_material = {m.material_id: {v.version_no: v.value for v in m.versions.all()} for m in dc_materials}
    
    parent_no, customer, color, resin, application, finished_product, dosage = "", "", "", "", "", "", ""
    if header.cm_no:
        parent_no, color = header.cm_no.cm_no, header.cm_no.color_desc
        formula_info = tbl_cmf_formula.objects.filter(cm_no=header.cm_no).first()
        if formula_info:
            customer, finished_product, dosage = formula_info.customer, formula_info.finished_product, formula_info.dosage
            processes = tbl_cmf_process02.objects.filter(cmf_formula_no=formula_info).values_list('process_no__name', flat=True)
            application = ", ".join(processes) if processes else formula_info.finished_product
        resin = ", ".join(tbl_resins_selected.objects.filter(cm_no=header.cm_no).values_list('resin_no__abbreviation', flat=True))
    elif header.rs_no:
        parent_no, customer, color, application, finished_product, dosage = header.rs_no.rs_no, header.rs_no.customer, header.rs_no.color_desc, header.rs_no.finished_product, header.rs_no.finished_product, header.rs_no.dosage
        resin = ", ".join(tbl_resins_selected.objects.filter(rs_no=header.rs_no).values_list('resin_no__abbreviation', flat=True))
    
    return {
        'header': header, 'dc_materials': dc_materials, 'versions_by_material': versions_by_material,
        'customer': customer, 'color': color, 'dosage': dosage, 'resin': resin,
        'application': application, 'finished_product': finished_product, 'parent_no': parent_no,
    }

@xframe_options_exempt
def print_dc_formula_preview(request, formula_id):
    """View to generate and serve the PDF."""
    try:
        data = _fetch_dc_formula_data(formula_id)
    except Exception as e:
        return HttpResponseServerError(f"Data Fetch Error: {str(e)}")

    template_abs_path = os.path.abspath(TEMPLATE_PATH)
    with _word_lock:
        with tempfile.TemporaryDirectory() as tmpdir:
            raw_pdf_path = os.path.join(tmpdir, "raw.pdf")
            final_pdf_path = os.path.join(tmpdir, "final.pdf")
            try:
                _fill_and_export_dc_formula_via_word(template_abs_path, raw_pdf_path, data)
                # Rescale and lock to Page 1
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