from datetime import datetime

from django.http import HttpResponse
import openpyxl
from openpyxl.styles import Font, Fill, PatternFill, Alignment
from django.db.models import Q
from main.models import *

def generate_feedback_excel(date_from=None, date_to=None):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Feedback Records"

    # Define Header
    headers = [
        "Matching No.", "Customer", "Date Created", "Date Lab Received", "Target Date",
        "Primary Color", "Color Description", "End Product", "Matching Type", "Salesman",
        "Color Req.", "Resin", "Process", "Type of Colorant", "Date Given Sample",
        "Set/PC", "Quantity Given", "Code Submitted", "Dosage", "Lot #", "AR #",
        "Date Standard & Result", "Comment", "Storage Details"
    ]

    # Gold, Accent 4, Lighter 40% is hex FFD966
    header_fill = PatternFill(start_color="FFD966", end_color="FFD966", fill_type="solid")
    header_font = Font(bold=True)

    for col_num, column_title in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num, value=column_title)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center")

    # Fetch Data
    feedback_qs = tbl_feedback_details.objects.select_related('cm_no', 'rs_no')
    
    # Filter by Date Created (using tbl_cmf_dates or RS date)
    if date_from and date_to:
        feedback_qs = feedback_qs.filter(
            Q(cm_no__tbl_cmf_dates__form_made__range=[date_from, date_to]) |
            Q(rs_no__date_created__range=[date_from, date_to])
        )

    row_num = 2
    for fb in feedback_qs:
        # Determine Parent
        parent = fb.cm_no if fb.cm_no else fb.rs_no
        is_cmf = True if fb.cm_no else False
        
        # 1. Basic Info
        matching_no = parent.cm_no if is_cmf else parent.rs_no
        
        # 2. Dates & Formula Info
        dates = None
        formula = None
        if is_cmf:
            dates = tbl_cmf_dates.objects.filter(cm_no=parent).first()
            formula = tbl_cmf_formula.objects.filter(cm_no=parent).first()
        
        # 3. Resin & Process Junctions
        resins = ", ".join(tbl_resins_selected.objects.filter(cm_no=parent if is_cmf else None, rs_no=parent if not is_cmf else None).values_list('resin_no__abbreviation', flat=True))
        processes = ", ".join(tbl_cmf_process02.objects.filter(cmf_formula_no=formula if is_cmf else None).values_list('process_no__name', flat=True))

        # 4. Color Logic
        primary_color = ""
        if is_cmf:
            primary_color = parent.in_code_no.color if parent.in_code_no else ""
        else:
            primary_color = parent.primary_color

        # 5. Final Code & Lot Info
        final_code = ""
        lot_no = "None"
        # Check MB first
        mb_final = tbl_mb_extruder_formula.objects.filter(cm_no=parent if is_cmf else None, rs_no=parent if not is_cmf else None, is_final=True).first()
        if mb_final:
            final_code = mb_final.code.product_code if mb_final.code else ""
            lot_no = mb_final.lot_no
        else:
            # Check DC
            dc_final = tbl_dc_extruder_formula.objects.filter(cm_no=parent if is_cmf else None, rs_no=parent if not is_cmf else None, is_final=True).first()
            if dc_final:
                final_code = dc_final.code.product_code if dc_final.code else ""

        # 6. AR Number
        status_rec = tbl_cmf_pending_completed.objects.filter(cm_no=parent if is_cmf else None, rs_no=parent if not is_cmf else None).first()

        data_row = [
            matching_no,
            formula.customer if formula else (parent.customer if not is_cmf else ""),
            dates.form_made.strftime('%m/%d/%Y') if dates and dates.form_made else (parent.date_created.strftime('%m/%d/%Y') if not is_cmf and parent.date_created else ""),
            dates.date_received_lab if dates else "",
            dates.due_date_lab.strftime('%m/%d/%Y') if dates and dates.due_date_lab else "",
            primary_color,
            parent.color_desc,
            formula.finished_product if formula else (parent.finished_product if not is_cmf else ""),
            parent.matching_type,
            parent.sm.name if is_cmf and parent.sm else (parent.sm_no.name if not is_cmf and parent.sm_no else ""),
            tbl_cmf_color_req.objects.filter(cm_no=parent if is_cmf else None).first().name if is_cmf else "",
            resins,
            processes,
            parent.colorant_type,
            fb.date_given_sample.strftime('%m/%d/%Y') if fb.date_given_sample else "",
            fb.pieces,
            fb.quantity_given,
            final_code,
            formula.dosage if formula else (parent.dosage if not is_cmf else ""),
            lot_no,
            status_rec.ar_no if status_rec else "",
            fb.date_sample_received.strftime('%m/%d/%Y') if fb.date_sample_received else "",
            fb.comment,
            fb.storage_details
        ]

        for col_idx, value in enumerate(data_row, 1):
            ws.cell(row=row_num, column=col_idx, value=value)
        row_num += 1

    # Auto-adjust columns
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except: pass
        ws.column_dimensions[column].width = max_length + 2

    return wb

def export_feedback_excel(request):
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
        pass

    wb = generate_feedback_excel(date_from, date_to)
    
    filename = f"Feedback_Report_{datetime.now().strftime('%Y%m%d')}.xlsx"
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    wb.save(response)
    
    return response