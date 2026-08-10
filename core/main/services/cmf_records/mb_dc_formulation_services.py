from django.http import JsonResponse
from main.models import tbl_cmf, tbl_cmf_formula, tbl_resins_selected, tbl_cmf_process02

def get_formulation_details(request):
    cm_no = request.GET.get('cm_no')
    cmf = tbl_cmf.objects.filter(cm_no=cm_no).first()
    
    if not cmf:
        return JsonResponse({'error': 'Not found'}, status=404)

    formula_info = tbl_cmf_formula.objects.filter(cm_no=cm_no).first()
    
    # Concatenate Resins
    resins = tbl_resins_selected.objects.filter(cm_no=cmf).values_list('resin_no__abbreviation', flat=True)
    resin_str = ", ".join(filter(None, resins))

    # Concatenate Processes
    processes = tbl_cmf_process02.objects.filter(cmf_formula_no=formula_info).values_list('process_no__name', flat=True)
    app_str = ", ".join(filter(None, processes))

    data = {
        'customer': formula_info.customer if formula_info else "",
        'resin': resin_str,
        'color': cmf.in_code_no.color if cmf.in_code_no else (cmf.color_desc or ""),
        'product_code': cmf.in_code_no.code if cmf.in_code_no else "",
        'dosage': formula_info.dosage if formula_info else "",
        'application': app_str,
        'finished_product': formula_info.finished_product if formula_info else "",
    }
    return JsonResponse(data)
