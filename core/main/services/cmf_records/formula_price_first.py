import io
import re
import json
from django.db.models import Max
from django.http import HttpResponse, JsonResponse
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment
from main.services.cmf_records import cmf_records_services # or local check
from main.models import tbl_cmf, tbl_cmf_formula, tbl_dc_extruder_formula, tbl_dc_extruder_formula02, tbl_mb_extruder_formula, tbl_mb_extruder_formula02, tbl_resins_selected

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


def download_price_first_excel(request):
    """
    Builds an .xlsx from the Price First modal's current rows, sent as
    JSON in the POST body (so it captures whatever the user typed into
    Remarks, not just the originally-fetched data). Built server-side
    with openpyxl since the app runs offline — no CDN-hosted client
    library involved.
    """
    payload = json.loads(request.body)
    rows = payload.get('rows', [])

    headers = [
        'Date', 'Customer', 'Class', 'Prod Code', 'Resin', 'Mat Code',
        'Mat Conc', 'End Product', 'Total', 'Others', 'Dosage',
        'Salesman', 'CMF No', 'HTML', 'C', 'M', 'Y', 'K', 'Remarks'
    ]

    wb = Workbook()
    ws = wb.active
    ws.title = 'Price First'

    ws.append(headers)
    for cell in ws[1]:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal='center')

    for row in rows:
        ws.append(row)

    for col_cells in ws.columns:
        max_len = max((len(str(c.value)) if c.value is not None else 0) for c in col_cells)
        ws.column_dimensions[col_cells[0].column_letter].width = min(max_len + 3, 40)

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    response = HttpResponse(
        buffer.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="PriceFirst.xlsx"'
    return response