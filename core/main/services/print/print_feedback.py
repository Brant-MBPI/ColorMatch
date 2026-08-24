import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from django.db.models import Q, Max
from django.http import HttpResponse
from datetime import datetime
from main.models import (
    tbl_feedback_details, tbl_cmf, tbl_rs, tbl_cmf_dates, 
    tbl_cmf_formula, tbl_cmf_pending_completed, tbl_resins_selected,
    tbl_cmf_process02, tbl_cmf_color_req, tbl_mb_extruder_formula,
    tbl_dc_extruder_formula
)

def generate_feedback_excel(date_from=None, date_to=None):
    """
    Generates a highly detailed Excel report for Feedback Records,
    applying specific styling and cross-referencing multiple tables.
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Feedback Records"

    # 1. Define Headers
    headers = [
        "Matching No.", "Customer", "Date Created", "Date Lab Received", "Target Date",
        "Primary Color", "Color Description", "End Product", "Matching Type", "Salesman",
        "Color Req.", "Resin", "Process", "Type of Colorant", "Date Given Sample",
        "Set/PC", "Quantity Given", "Code Submitted", "Dosage", "Lot #", "AR #",
        "Date Standard & Result", "Comment", "Storage Details"
    ]

    # 2. Define Styling (Gold, Accent 4, Lighter 40% is hex FFD966)
    header_fill = PatternFill(start_color="FFD966", end_color="FFD966", fill_type="solid")
    header_font = Font(bold=True)
    center_align = Alignment(horizontal="center", vertical="center")

    for col_num, column_title in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num, value=column_title)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = center_align

    # 3. Fetch Data
    feedback_qs = tbl_feedback_details.objects.select_related('cm_no', 'rs_no').all()
    
    # Apply Date Filters based on parent creation date
    if date_from and date_to:
        feedback_qs = feedback_qs.filter(
            Q(cm_no__tbl_cmf_dates__form_made__range=[date_from, date_to]) |
            Q(rs_no__date_created__range=[date_from, date_to])
        )

    row_num = 2
    for fb in feedback_qs:
        # --- Identify Parent Type ---
        is_cmf = True if fb.cm_no else False
        parent = fb.cm_no if is_cmf else fb.rs_no
        
        if not parent:
            continue

        # --- Data Gathering ---
        matching_no = parent.cm_no if is_cmf else parent.rs_no
        
        # Cross-reference related models
        dates = tbl_cmf_dates.objects.filter(cm_no=parent if is_cmf else None, rs_no=parent if not is_cmf else None).first()
        pending = tbl_cmf_pending_completed.objects.filter(cm_no=parent if is_cmf else None, rs_no=parent if not is_cmf else None).first()
        
        if is_cmf:
            formula = tbl_cmf_formula.objects.filter(cm_no=parent).first()
            customer = formula.customer if formula else ""
            end_product = formula.finished_product if formula else ""
            dosage = formula.dosage if formula else ""
            salesman = parent.sm.name if parent.sm else ""
            color_req = tbl_cmf_color_req.objects.filter(cm_no=parent).first()
            color_req_val = color_req.name if color_req else ""
            primary_color = parent.in_code_no.color if parent.in_code_no else ""
            process_list = tbl_cmf_process02.objects.filter(cmf_formula_no=formula).values_list('process_no__name', flat=True) if formula else []
        else:
            customer = parent.customer or ""
            end_product = parent.finished_product or ""
            dosage = parent.dosage or ""
            salesman = parent.sm_no.name if parent.sm_no else ""
            color_req = tbl_cmf_color_req.objects.filter(rs_no=parent).first()
            color_req_val = color_req.name if color_req else ""
            primary_color = parent.primary_color or ""
            process_list = tbl_cmf_process02.objects.filter(rs_no=parent).values_list('process_no__name', flat=True)

        # Resin & Process concatenation
        resins = ", ".join(tbl_resins_selected.objects.filter(cm_no=parent if is_cmf else None, rs_no=parent if not is_cmf else None).values_list('resin_no__abbreviation', flat=True))
        processes = ", ".join(process_list)

        # Final Code & Lot logic
        code_submitted = ""
        lot_no = "None"
        
        # Check for final formula (MB then DC)
        final_mb = tbl_mb_extruder_formula.objects.filter(cm_no=parent if is_cmf else None, rs_no=parent if not is_cmf else None, is_final=True).select_related('code').first()
        if final_mb:
            code_submitted = final_mb.code.product_code if final_mb.code else ""
            lot_no = final_mb.lot_no or "None"
        else:
            final_dc = tbl_dc_extruder_formula.objects.filter(cm_no=parent if is_cmf else None, rs_no=parent if not is_cmf else None, is_final=True).select_related('code').first()
            if final_dc:
                code_submitted = final_dc.code.product_code if final_dc.code else ""
                lot_no = "None" # As per requirement, DC shows None for lot

        # --- Map Row Data ---
        data_row = [
            matching_no,
            customer,
            dates.form_made.strftime('%m/%d/%Y') if dates and dates.form_made else (parent.date_created.strftime('%m/%d/%Y') if not is_cmf and parent.date_created else ""),
            dates.date_received_lab if dates else "",
            dates.due_date_lab.strftime('%m/%d/%Y') if dates and dates.due_date_lab else "",
            primary_color,
            parent.color_desc or "",
            end_product,
            parent.matching_type or "",
            salesman,
            color_req_val,
            resins,
            processes,
            parent.colorant_type or "",
            pending.date_submitted.strftime('%m/%d/%Y') if pending.date_submitted else "",
            fb.pieces or "",
            fb.quantity_given or "",
            code_submitted,
            dosage,
            lot_no,
            pending.ar_no if pending else "",
            fb.date_sample_received.strftime('%m/%d/%Y') if fb.date_sample_received else "",
            fb.comment or "",
            fb.storage_details or ""
        ]

        for col_idx, value in enumerate(data_row, 1):
            ws.cell(row=row_num, column=col_idx, value=value)
        row_num += 1

    # 4. Auto-Adjust Columns and Apply Borders
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except: pass
        ws.column_dimensions[column].width = min(max_length + 2, 50) # Cap width at 50

    return wb

def export_feedback_excel(request):
    """
    View handler for exporting the feedback report.
    Expects 'from' and 'to' query parameters in MM/DD/YYYY format.
    """
    from_date_str = request.GET.get('from')
    to_date_str = request.GET.get('to')
    
    date_from = None
    date_to = None
    
    try:
        if from_date_str:
            date_from = datetime.strptime(from_date_str, '%m/%d/%Y').date()
        if to_date_str:
            date_to = datetime.strptime(to_date_str, '%m/%d/%Y').date()
    except ValueError:
        pass # If dates are invalid, the generate function returns all records

    wb = generate_feedback_excel(date_from, date_to)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"Feedback_Report_{timestamp}.xlsx"
    
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    wb.save(response)
    
    return response