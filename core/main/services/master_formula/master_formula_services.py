from django.core.cache import cache
from django.utils import timezone
import json
from datetime import datetime
from django.db import transaction
from django.http import JsonResponse
from django.db.models import Max
from django.shortcuts import render
from main.services.cmf_records import cmf_records_services
from main.models import (
    tbl_cmf_formula, tbl_cmf_process02, tbl_dc_extruder_formula, tbl_dc_extruder_formula02, tbl_master_formula, tbl_master_formula_info, 
    tbl_master_formula_encode, tbl_cmf, tbl_mb_extruder_formula, tbl_mb_extruder_formula02, tbl_resins_selected, tbl_rs
)
from django.contrib.auth import get_user_model 
User = get_user_model()

# Cache list
# 'master_formula_records_list' 
# 'matching_numbers_list' 
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
        'total_concentration': formula.total_concentration if formula.total_concentration is not None else '0.000000',
        'sum_of_concentration': formula.dosage if formula.dosage is not None else '0.000000',
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
    records = cache.get('master_formula_records_list')
    
    if not records:
        # Fetch from DB if cache is empty
        qs = tbl_master_formula.objects.filter(is_deleted=False).order_by('-form_id').values(
            'form_id', 'index_no', 'customer', 'product_code', 'prod_color', 'total_concentration', 'ld'
        )
        records = list(qs)
        cache.set('master_formula_records_list', records, CACHE_TIMEOUT)
        
    return records

def get_all_matching_numbers():
    """
    Fetches all unique CM and RS numbers from the database with Caching.
    Used for the Matching No. TomSelect.
    """
    nos = cache.get('matching_numbers_list')
    
    if not nos:
        # Get CMF numbers (exclude nulls/empties)
        cmf_nos = list(tbl_cmf.objects.exclude(cm_no__isnull=True).exclude(cm_no='').values_list('cm_no', flat=True))
        # Get RS numbers (exclude nulls/empties)
        rs_nos = list(tbl_rs.objects.exclude(rs_no__isnull=True).exclude(rs_no='').values_list('rs_no', flat=True))
        
        # Combine, unique-ify, and sort
        nos = sorted(list(set(cmf_nos + rs_nos)))
        cache.set('matching_numbers_list', nos, CACHE_TIMEOUT)
        
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
    # cache.delete('master_formula_records_list')
    # cache.delete('matching_numbers_list')

def save_master_formula(request):
    """Handles creating or updating a Master Formula and updating source MB/DC."""
    try:
        with transaction.atomic():
            data = request.POST
            form_id = data.get('form_id')
            is_new = data.get('is_new_flag') == 'true'
            
            # 1. Get or Create Master Formula
            if not is_new and form_id:
                mf = tbl_master_formula.objects.get(pk=form_id)
            else:
                mf = tbl_master_formula()

            # 2. Map Fields
            mf.customer = data.get('customer')
            mf.index_no = data.get('index_no')
            mf.product_code = data.get('product_code')
            mf.prod_color = data.get('prod_color')
            # Mapping based on your specific requirements:
            mf.total_concentration = data.get('total_concentration') or 0
            mf.dosage = data.get('sum_of_concentration') or 0
            mf.ld = data.get('dosage') or 0
            mf.mix_time = data.get('mix_time')
            mf.resin = data.get('resin')
            mf.application = data.get('application')
            mf.cm_no = data.get('cm_no')
            mf.notes = data.get('notes')
            mf.html_code_hex = data.get('html_code_hex')
            mf.cyan = data.get('cyan') or None
            mf.magenta = data.get('magenta') or None
            mf.yellow = data.get('yellow') or None
            mf.black = data.get('black') or None
            
            dt_str = data.get('colormatch_date')
            if dt_str:
                try:
                    mf.colormatch_date = datetime.strptime(dt_str, '%m/%d/%Y').date()
                except ValueError:
                    pass
            
            mf.date_time = timezone.now().strftime('%m/%d/%Y %I:%M %p')
            mf.save()

            # 3. Handle Materials
            tbl_master_formula_info.objects.filter(form=mf).delete()
            materials_json = data.get('materials_data')
            if materials_json:
                materials = json.loads(materials_json)
                for i, mat in enumerate(materials):
                    tbl_master_formula_info.objects.create(
                        form=mf,
                        sequence_no=i + 1,
                        material_code=mat['material'],
                        concentration=mat['concentration']
                    )

            # 4. Handle Metadata
            encode, _ = tbl_master_formula_encode.objects.get_or_create(form=mf)
            encode.match_by = data.get('matched_by')
            encode.encoded_by = data.get('encoded_by')
            encode.updated_by = request.user.first_name if request.user.is_authenticated else "System"
            encode.save()

            # 5. Update Source Formula (MB or DC)
            source_pk = data.get('source_formula_pk')
            source_type = data.get('source_formula_type')
            if source_pk and source_type:
                if source_type == 'MB':
                    tbl_mb_extruder_formula.objects.filter(pk=source_pk).update(in_master_formula=True)
                elif source_type == 'DC':
                    tbl_dc_extruder_formula.objects.filter(pk=source_pk).update(in_master_formula=True)

            cache.delete('master_formula_records_list')
            return True, mf.form_id
    except Exception as e:
        return False, str(e)


# For formula  lookup
def master_formula_lookup(request):
    matching_no = request.GET.get('matching_no', '').strip()
    error = None
    mb_list = []
    dc_list = []
    
    # Parent Details object to be used by all formulas under this Matching No.
    parent = {
        'customer': '',
        'resin_used': '',
        'colorant_type': '',
        'process': '',
    }
    color = ''
    if not matching_no:
        error = "No matching number provided."
    else:
        cmf = tbl_cmf.objects.filter(cm_no=matching_no).first()
        rs = None
        if not cmf:
            rs = tbl_rs.objects.filter(rs_no=matching_no).first()

        if not cmf and not rs:
            error = f'No CMF or RS record found for "{matching_no}".'
        else:
            # 1. GET PARENT DETAILS (CMF or RS)
            if cmf:
                formula_info = tbl_cmf_formula.objects.filter(cm_no=cmf).first()
                parent['customer'] = formula_info.customer if formula_info else ""
                parent['colorant_type'] = cmf.colorant_type or ""
                
                # Resins (Concatenated)
                resins = tbl_resins_selected.objects.filter(cm_no=cmf).values_list('resin_no__abbreviation', flat=True)
                parent['resin_used'] = ", ".join(filter(None, resins))
                
                # Process/Application (Concatenated)
                processes = tbl_cmf_process02.objects.filter(cmf_formula_no=formula_info).values_list('process_no__name', flat=True)
                parent['process'] = ", ".join(filter(None, processes))
                
                mb_qs = tbl_mb_extruder_formula.objects.filter(cm_no=cmf).select_related('code')
                dc_qs = tbl_dc_extruder_formula.objects.filter(cm_no=cmf).select_related('code')
                color = cmf.in_code_no.color if cmf.in_code_no else (cmf.color_desc or '---')
            else:
                parent['customer'] = rs.customer or ""
                parent['colorant_type'] = rs.colorant_type or ""
                
                # Resins
                resins = tbl_resins_selected.objects.filter(rs_no=rs).values_list('resin_no__abbreviation', flat=True)
                parent['resin_used'] = ", ".join(filter(None, resins))
                
                # Process
                processes = tbl_cmf_process02.objects.filter(rs_no=rs).values_list('process_no__name', flat=True)
                parent['process'] = ", ".join(filter(None, processes))

                mb_qs = tbl_mb_extruder_formula.objects.filter(rs_no=rs).select_related('code')
                dc_qs = tbl_dc_extruder_formula.objects.filter(rs_no=rs).select_related('code')
                color = rs.primary_color or rs.color_desc or '---'

            # 2. PROCESS MB FORMULAS
            for f in mb_qs:
                ingredients_objs = tbl_mb_extruder_formula02.objects.filter(mb=f)
                ingredients = [
                    {'material': ing.material, 'value': float(ing.value) if ing.value is not None else 0}
                    for ing in ingredients_objs
                ]
                # Calculate Sum of Concentration
                sum_con = sum(item['value'] for item in ingredients)

                mb_list.append({
                    'header': f,
                    'pk': f.mb_no,
                    'ingredients': ingredients,
                    'sum_con': format(sum_con, ".6f"),
                    'script_id': f'mf-ing-mb-{f.pk}'
                })

            # 3. PROCESS DC FORMULAS
            for f in dc_qs:
                ingredients_objs = tbl_dc_extruder_formula02.objects.filter(dc=f)
                ingredients = [
                    {'material': ing.material, 'value': float(ing.value) if ing.value is not None else 0}
                    for ing in ingredients_objs
                ]
                sum_con = sum(item['value'] for item in ingredients)

                dc_list.append({
                    'header': f,
                    'pk': f.dc_no,
                    'ingredients': ingredients,
                    'sum_con': format(sum_con, ".6f"),
                    'script_id': f'mf-ing-dc-{f.pk}'
                })
    
    context = {
        'matching_no': matching_no,
        'error': error,
        'color': color,
        'parent': parent, # New: Parent details
        'mb_formulas': mb_list,
        'dc_formulas': dc_list,
    }
    return render(request, "modal/master-formula/master_formula_lookup.html", context)
