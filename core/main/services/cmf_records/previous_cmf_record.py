from django.http import JsonResponse
import re

from main.models import tbl_cmf

def check_previous_matching(request):
    cm_no_input = request.GET.get('cm_no', '').strip()
    if not cm_no_input:
        return JsonResponse({'match': False, 'exists_exact': False})

    exists_exact = tbl_cmf.objects.filter(cm_no=cm_no_input).exists()

    # Logic: If user types "A9248b", base is "A9248"
    #. Logic for suggestions (Previous Matching)
    # Only trigger this if the input ends in a letter (e.g., 'A915a')
    match_found = False
    latest_cm_no = None

    if re.search(r'[a-zA-Z]$', cm_no_input):
        # Extract base (e.g., 'A915a' -> 'A915')
        base = re.sub(r'[a-zA-Z]$', '', cm_no_input)
        
        # Look for the original or other versions
        latest_record = tbl_cmf.objects.filter(
            cm_no__startswith=base
        ).exclude(cm_no=cm_no_input).order_by('-cm_no').first()

        if latest_record:
            match_found = True
            latest_cm_no = latest_record.cm_no

    return JsonResponse({
        'exists_exact': exists_exact,
        'match': match_found,
        'latest_cm_no': latest_cm_no
    })