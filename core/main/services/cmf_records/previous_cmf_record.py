from django.http import JsonResponse
import re

from main.models import tbl_cmf

def check_previous_matching(request):
    cm_no_input = request.GET.get('cm_no', '').strip()
    if not cm_no_input:
        return JsonResponse({'match': False, 'exists_exact': False})

    # 1. HARD VALIDATION: Exact record exists
    exists_exact = tbl_cmf.objects.filter(cm_no=cm_no_input).exists()

    # 2. SEQUENTIAL VALIDATION (c through z)
    sequential_error = None
    # This regex captures the base part and the last letter suffix (e.g., 'A9151', 'c')
    match_parts = re.match(r'^(.+)([a-zA-Z])$', cm_no_input)
    
    if match_parts:
        base, suffix = match_parts.groups()
        suffix = suffix.lower()

        # Check only if suffix is 'c' or higher
        if 'c' <= suffix <= 'z':
            # Calculate previous letter (e.g., if 'c', get 'b')
            prev_suffix = chr(ord(suffix) - 1)
            prev_cm_no = f"{base}{prev_suffix}"

            # Check if the required previous version exists (case-insensitive)
            if not tbl_cmf.objects.filter(cm_no__iexact=prev_cm_no).exists():
                sequential_error = f"Cannot create '{cm_no_input}'. The previous version '{prev_cm_no}' must exist first."

    # 3. SUGGESTION LOGIC (Only run if no sequential error and doesn't exist yet)
    match_found = False
    latest_cm_no = None
    if not sequential_error and not exists_exact:
        if re.search(r'[a-zA-Z]$', cm_no_input):
            base_sug = re.sub(r'[a-zA-Z]$', '', cm_no_input)
            latest_record = tbl_cmf.objects.filter(
                cm_no__startswith=base_sug
            ).exclude(cm_no=cm_no_input).order_by('-cm_no').first()
            
            if latest_record:
                match_found = True
                latest_cm_no = latest_record.cm_no

    return JsonResponse({
        'exists_exact': exists_exact,
        'sequential_error': sequential_error, # New validation message
        'match': match_found,
        'latest_cm_no': latest_cm_no
    })