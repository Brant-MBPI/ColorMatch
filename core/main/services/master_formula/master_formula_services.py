from django.core.cache import cache
from django.http import JsonResponse
from django.db.models import Max
from main.services.cmf_records import cmf_records_services
from main.models import (
    tbl_master_formula, tbl_master_formula_info, 
    tbl_master_formula_encode, tbl_cmf, tbl_rs
)
from django.contrib.auth import get_user_model 
User = get_user_model()

# Cache Keys
CACHE_KEY_RECORDS = 'master_formula_records_list'
CACHE_KEY_MATCHING_NOS = 'matching_numbers_list'
CACHE_TIMEOUT = 3600  # 1 hour

def get_master_formula_details(form_id):
    """Fetches full details for a single master formula."""
    formula = tbl_master_formula.objects.filter(pk=form_id, is_deleted=False).first()
    if not formula:
        return None

    encode = tbl_master_formula_encode.objects.filter(form=formula).first()
    materials = list(
        tbl_master_formula_info.objects.filter(form=formula, is_deleted=False)
        .order_by('sequence_no')
        .values('material_code', 'concentration')
    )

    return {
        'form_id': formula.form_id,
        'index_no': formula.index_no or '',
        'customer': formula.customer or '',
        'product_code': formula.product_code or '',
        'prod_color': formula.prod_color or '',
        'total_concentration': formula.dosage if formula.dosage is not None else '0.000000',
        'dosage': formula.ld if formula.ld is not None else '',
        'mix_time': formula.mix_time or '',
        'resin': formula.resin or '',
        'application': formula.application or '',
        'cm_no': formula.cm_no or '',
        'colormatch_date': formula.colormatch_date.strftime('%m/%d/%Y') if formula.colormatch_date else '',
        'notes': formula.notes or '',
        'html_code_hex': formula.html_code_hex or '',
        'cyan': formula.cyan if formula.cyan is not None else '',
        'magenta': formula.magenta if formula.magenta is not None else '',
        'yellow': formula.yellow if formula.yellow is not None else '',
        'black': formula.black if formula.black is not None else '',
        'updated_by': encode.updated_by if encode else '',
        'date_time': formula.date_time or '',
        'matched_by': encode.match_by if encode else '',
        'encoded_by': encode.encoded_by if encode else '',
        'materials': materials,
    }

def get_master_formula_list():
    """Fetches all records list with Caching."""
    records = cache.get(CACHE_KEY_RECORDS)
    
    if not records:
        # Fetch from DB if cache is empty
        qs = tbl_master_formula.objects.filter(is_deleted=False).order_by('-form_id').values(
            'form_id', 'index_no', 'customer', 'product_code', 'prod_color', 'total_concentration', 'ld'
        )
        records = list(qs)
        cache.set(CACHE_KEY_RECORDS, records, CACHE_TIMEOUT)
        
    return records

def get_all_matching_numbers():
    """
    Fetches all unique CM and RS numbers from the database with Caching.
    Used for the Matching No. TomSelect.
    """
    nos = cache.get(CACHE_KEY_MATCHING_NOS)
    
    if not nos:
        # Get CMF numbers (exclude nulls/empties)
        cmf_nos = list(tbl_cmf.objects.exclude(cm_no__isnull=True).exclude(cm_no='').values_list('cm_no', flat=True))
        # Get RS numbers (exclude nulls/empties)
        rs_nos = list(tbl_rs.objects.exclude(rs_no__isnull=True).exclude(rs_no='').values_list('rs_no', flat=True))
        
        # Combine, unique-ify, and sort
        nos = sorted(list(set(cmf_nos + rs_nos)))
        cache.set(CACHE_KEY_MATCHING_NOS, nos, CACHE_TIMEOUT)
        
    return nos

def master_formula_materials_json(request, form_id):
    formula = tbl_master_formula.objects.filter(pk=form_id).first()
    
    if not formula:
        return JsonResponse({'error': 'Record not found'}, status=404)
    
    materials = list(
        tbl_master_formula_info.objects.filter(form_id=form_id, is_deleted=False)
        .order_by('sequence_no')
        .values('material_code', 'concentration')
    )
    response_data = {
        'form_id': formula.form_id,
        'index_no': formula.index_no or '-',
        'customer': formula.customer or '',
        'materials': materials
    }
    return JsonResponse(response_data, safe=False)

def get_master_formula_context(form_id=None):
    """Combines all data needed for the Master Formula page context."""
    
    if form_id:
        form_data = get_master_formula_details(form_id)
    else:
        # --- CALCULATE NEXT ID FOR NEW RECORDS ---
        max_id = tbl_master_formula.objects.aggregate(Max('form_id'))['form_id__max'] or 0
        form_data = {
            'form_id': max_id + 1,
            'is_new': True
        }
    
    return {
        'form_data': form_data,
        'master_formula_records': get_master_formula_list(),
        'matching_numbers': get_all_matching_numbers(), # Added cached matching numbers
        'users': list(User.objects.filter(is_active=True).exclude(first_name="").values_list('first_name', flat=True).distinct().order_by('first_name')),
        'materials': cmf_records_services.get_raw_material_codes(),
        'customers': ["Masterbatch PH", "Generic Co."],
    }

    # """
    # Clears all caches related to Master Formula.
    # Call this when syncing legacy data or saving new formulas.
    # """
    # cache.delete(CACHE_KEY_RECORDS)
    # cache.delete(CACHE_KEY_MATCHING_NOS)