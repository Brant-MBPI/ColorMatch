from django.http import JsonResponse
import re

from main.models import tbl_cmf

def check_previous_matching(request):
    cm_no_input = request.GET.get('cm_no', '').strip()
    if not cm_no_input:
        return JsonResponse({'match': False})

    # Logic: If user types "A9248b", base is "A9248"
    # This regex removes the last character if it's a letter
    base = re.sub(r'[a-zA-Z]$', '', cm_no_input)

    # Search for any record that starts with the base but IS NOT the exact input
    latest_record = tbl_cmf.objects.filter(
        cm_no__startswith=base
    ).exclude(cm_no=cm_no_input).order_by('-cm_no').first()

    if latest_record:
        return JsonResponse({
            'match': True,
            'latest_cm_no': latest_record.cm_no
        })
    
    return JsonResponse({'match': False})