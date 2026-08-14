import os
import tempfile
import threading
import uuid
from decimal import Decimal

import pythoncom
import win32com.client as win32
from django.contrib import messages
from django.http import HttpResponse, HttpResponseServerError
from django.shortcuts import redirect
from django.views.decorators.clickjacking import xframe_options_exempt

from main.services.print.print_util import _resize_pdf_to_fixed_size
from main.models import (
    tbl_dc_extruder_formula, tbl_dc_extruder_formula02,
    tbl_cmf_formula, tbl_resins_selected,
)

# Word COM automation isn't safe to run from multiple threads/requests at
# once, same reasoning as the Excel lock. Kept separate since Word and
# Excel COM apps are independent processes.
_word_lock = threading.Lock()

DC_TEMPLATE_PATH = os.path.join('main', 'templates', 'print_excel', 'dc_formula_template.docx')

# --- UPDATED TO LETTER LANDSCAPE ---
DC_PDF_WIDTH_IN = 11.0   # Letter Width (Landscape)
DC_PDF_HEIGHT_IN = 8.5   # Letter Height (Landscape)

MATERIAL_START_ROW = 2   # row 1 is the header row ("MATERIAL", "1", "2", ...)
MATERIAL_MAX_ROWS = 10
MATERIALS_TABLE_INDEX = 2  # 1-based: table 1 = header info, table 2 = materials


def _fetch_dc_formula_data(formula_id):
    """Pulls the header, its ingredient rows, and customer/resin/color/
    application/finished_product from whichever parent (CMF or RS) it
    belongs to."""
    header = tbl_dc_extruder_formula.objects.select_related('cm_no', 'rs_no', 'code').get(pk=formula_id)
    ingredients = list(
        tbl_dc_extruder_formula02.objects.filter(dc=header).order_by('id')[:MATERIAL_MAX_ROWS]
    )

    customer = ""
    color = ""
    resin = ""
    application = ""
    finished_product = ""
    parent_no = ""
    dosage = ""

    if header.cm_no:
        parent_no = header.cm_no.cm_no
        color = header.cm_no.color_desc

        formula_info = tbl_cmf_formula.objects.filter(cm_no=header.cm_no).first()
        if formula_info:
            customer = formula_info.customer
            application = formula_info.finished_product
            finished_product = formula_info.finished_product
            dosage = formula_info.dosage

        resin = ", ".join(
            tbl_resins_selected.objects.filter(cm_no=header.cm_no).values_list('resin_no__abbreviation', flat=True)
        )

    elif header.rs_no:
        parent_no = header.rs_no.rs_no
        customer = header.rs_no.customer
        color = header.rs_no.color_desc
        application = header.rs_no.finished_product
        finished_product = header.rs_no.finished_product
        dosage = header.rs_no.dosage

        resin = ", ".join(
            tbl_resins_selected.objects.filter(rs_no=header.rs_no).values_list('resin_no__abbreviation', flat=True)
        )

    return {
        'header': header,
        'ingredients': ingredients,
        'customer': customer,
        'color': color,
        'dosage': dosage,
        'resin': resin,
        'application': application,
        'finished_product': finished_product,
        'parent_no': parent_no,
    }


def _to_num(val):
    if val is None or val == "":
        return 0
    if isinstance(val, Decimal):
        return float(val)
    try:
        return float(val)
    except (TypeError, ValueError):
        return 0


def _set_bookmark(doc, name, value):
    """
    Writes text into a bookmark's range, then re-adds the bookmark
    (Word deletes it when .Text is set directly). Silently skips
    bookmarks that don't exist in the template rather than erroring,
    so a missing/renamed bookmark doesn't crash the whole export —
    check server logs / the printed PDF if a field looks blank.
    """
    text = "" if value is None else str(value)
    if doc.Bookmarks.Exists(name):
        rng = doc.Bookmarks(name).Range
        rng.Text = text
        doc.Bookmarks.Add(name, rng)
    else:
        print(f"WARNING: bookmark '{name}' not found in DC template.")


def _fill_and_export_dc_formula_via_word(template_abs_path, pdf_path, data):
    header = data['header']
    ingredients = data['ingredients']

    pythoncom.CoInitialize()
    word = None
    doc = None
    try:
        word = win32.DispatchEx("Word.Application")
        word.Visible = False
        word.DisplayAlerts = False

        doc = word.Documents.Open(template_abs_path)
        # --- FORCE PAGE SETUP TO LANDSCAPE LETTER ---
        # wdOrientLandscape = 1, wdPaperLetter = 1
        try:
            doc.PageSetup.Orientation = 1  # wdOrientLandscape
            doc.PageSetup.PageWidth = 11.0 * 72
            doc.PageSetup.PageHeight = 8.5 * 72
        except Exception as e:
            # If the printer driver is extremely restrictive, 
            # we log the warning but allow it to continue with the template's defaults
            print(f"Warning: Could not force PageSetup dimensions: {e}")


        # --- HEADER FIELDS (bookmarks) ---
        _set_bookmark(doc, 'code', header.code.product_code if header.code else "")
        _set_bookmark(doc, 'cmf', data['parent_no'])
        _set_bookmark(doc, 'customer', data['customer'])
        _set_bookmark(doc, 'resin', data['resin'])
        _set_bookmark(doc, 'color', data['color'])
        _set_bookmark(doc, 'date_matched', header.date.strftime('%m/%d/%Y') if header.date else "")
        _set_bookmark(doc, 'dosage', f"{_to_num(data['dosage']):.2f}%" if 'dosage' in data else "")
        _set_bookmark(doc, 'sample_size', header.sample_size)
        _set_bookmark(doc, 'product_used', getattr(header, 'product_used', ''))
        _set_bookmark(doc, 'mixing_time', header.mixing_time)
        _set_bookmark(doc, 'application', data['application'])
        _set_bookmark(doc, 'product_used', data['finished_product'])
        _set_bookmark(doc, 'note', header.notes)
        _set_bookmark(doc, 'matched_by', header.matched_by)
        _set_bookmark(doc, 'weighed_by', header.weighted_by)
        _set_bookmark(doc, 'encoded_by', header.encoded_by)

        # --- MATERIALS TABLE ---
        # Only columns A (Material), B ("1" -> value), C ("2" -> weight)
        # are touched; columns D-K are left as-is.
        table = doc.Tables(MATERIALS_TABLE_INDEX)
        total_value = Decimal('0')

        for i in range(MATERIAL_MAX_ROWS):
            row_num = MATERIAL_START_ROW + i
            if i < len(ingredients):
                ing = ingredients[i]
                table.Cell(row_num, 1).Range.Text = ing.material or ""
                table.Cell(row_num, 2).Range.Text = f"{_to_num(ing.value):.4f}"
                table.Cell(row_num, 3).Range.Text = f"{_to_num(ing.weight):.7f}"
                total_value += Decimal(ing.value or 0)
            else:
                table.Cell(row_num, 1).Range.Text = ""
                table.Cell(row_num, 2).Range.Text = ""
                table.Cell(row_num, 3).Range.Text = ""

        # --- TOTALS (bookmarks you're adding) ---
        _set_bookmark(doc, 'total_value', f"{_to_num(total_value):.4f}")
        _set_bookmark(doc, 'total_weight', f"{_to_num(header.total_weight):.7f}")

        # 17 = wdFormatPDF
        doc.SaveAs(pdf_path, FileFormat=17)

    finally:
        if doc is not None:
            doc.Close(SaveChanges=False)   # never overwrite the template
        if word is not None:
            word.Quit()
        pythoncom.CoUninitialize()


def print_dc_formula_preview(request, formula_id):
    """
    Fills the ORIGINAL DC Formula Word template via COM (bookmarks for
    header fields, direct cell addressing for the materials table),
    exports to PDF, resizes to a fixed page size, and serves it inline
    for browser preview. All temp files are cleaned up before returning.
    """
    try:
        data = _fetch_dc_formula_data(formula_id)
    except tbl_dc_extruder_formula.DoesNotExist:
        messages.error(request, f"Error: DC Formula '{formula_id}' was not found.")
        return redirect('cmf_entry')
    except Exception as e:
        messages.error(request, f"System Error: {str(e)}")
        return redirect('cmf_entry')

    template_abs_path = os.path.abspath(DC_TEMPLATE_PATH)
    if not os.path.exists(template_abs_path):
        return HttpResponseServerError("Template file not found on server.")

    with tempfile.TemporaryDirectory() as tmpdir:
        raw_pdf_path = os.path.join(tmpdir, f"{uuid.uuid4().hex}_raw.pdf")
        final_pdf_path = os.path.join(tmpdir, f"{uuid.uuid4().hex}_final.pdf")

        try:
            with _word_lock:
                _fill_and_export_dc_formula_via_word(template_abs_path, raw_pdf_path, data)
            _resize_pdf_to_fixed_size(
                raw_pdf_path, final_pdf_path,
                width_in=DC_PDF_WIDTH_IN, height_in=DC_PDF_HEIGHT_IN,
            )
        except Exception as e:
            return HttpResponseServerError(f"PDF export failed: {str(e)}")

        if not os.path.exists(final_pdf_path):
            return HttpResponseServerError("PDF export failed: no output file produced.")

        with open(final_pdf_path, 'rb') as f:
            pdf_bytes = f.read()

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = 'inline'
    response['X-Frame-Options'] = 'SAMEORIGIN'
    return response


print_dc_formula_preview = xframe_options_exempt(print_dc_formula_preview)