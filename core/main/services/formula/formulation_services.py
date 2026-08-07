from django.core.cache import cache
from django.db.models.functions import Concat
from django.utils import timezone
import json
from datetime import datetime
from django.db import transaction
from django.http import JsonResponse
from django.db.models import Max, Value
from django.shortcuts import render
from main.utils.log_audit_trail import log_audit
from main.services.cmf_records import cmf_records_services
from main.models import (
    tbl_formula01, tbl_formula02, tbl_formula_encode,
    tbl_cmf, tbl_rs, tbl_resins_selected, tbl_cmf_process02, tbl_cmf_formula,
    tbl_mb_extruder_formula, tbl_mb_extruder_formula02,
    tbl_dc_extruder_formula, tbl_dc_extruder_formula02
)
from django.contrib.auth import get_user_model 
User = get_user_model()

# Cache settings
CACHE_TIMEOUT = 3600  # 1 hour

def get_formulation_details(form_id):
    """Fetches full details for a single formulation record."""
    f = tbl_formula01.objects.filter(pk=form_id, is_deleted=False).first()
    if not f:
        return None

    encode = tbl_formula_encode.objects.filter(form=f).first()
    materials = list(
        tbl_formula02.objects.filter(form=f, is_deleted=False)
        .order_by('sequence_no')
        .values('material_code', 'concentration')
    )

    return {
        'form_id': f.form_id,
        'index_no': f.index_no or '',
        'customer': f.customer or '',
        'product_code': f.prod_code or '',
        'prod_color': f.prod_color or '',
        'total_concentration': f.total_concentration if f.total_concentration is not None else '0.000000',
        'sum_of_concentration': f.dosage if f.dosage is not None else '0.000000',
        'dosage': f.ld if f.ld is not None else '',
        'mix_time': f.mix_time or '',
        'resin': f.resin or '',
        'application': f.application or '',
        'cm_no': f.colormatch_no or '',
        'colormatch_date': f.colormatch_date.strftime('%m/%d/%Y') if f.colormatch_date else '',
        'notes': f.notes or '',
        'updated_by': encode.updated_by if encode else '',
        'updated_time': f.date_time or '',
        'matched_by': encode.match_by if encode else '',
        'encoded_by': encode.encoded_by if encode else '',
        'materials': materials,
    }

def get_formulation_list():
    """Fetches all formulation records with Caching."""
    records = cache.get('formulation_records_list')
    
    if not records:
        qs = tbl_formula01.objects.filter(is_deleted=False).order_by('-form_id').values(
            'form_id', 'index_no', 'customer', 'prod_code', 'prod_color', 'total_concentration', 'ld'
        )
        records = list(qs)
        cache.set('formulation_records_list', records, CACHE_TIMEOUT)
        
    return records

def get_all_matching_numbers():
    """Fetches all unique CM and RS numbers for TomSelect."""
    nos = cache.get('matching_numbers_list')
    
    if not nos:
        cmf_nos = list(tbl_cmf.objects.exclude(cm_no__isnull=True).exclude(cm_no='').values_list('cm_no', flat=True))
        rs_nos = list(tbl_rs.objects.exclude(rs_no__isnull=True).exclude(rs_no='').values_list('rs_no', flat=True))
        nos = sorted(list(set(cmf_nos + rs_nos)))
        cache.set('matching_numbers_list', nos, CACHE_TIMEOUT)
        
    return nos

def formulation_materials_json(request, form_id):
    """API for materials breakdown."""
    formula = tbl_formula01.objects.filter(pk=form_id).first()
    if not formula:
        return JsonResponse({'error': 'Record not found'}, status=404)
    
    materials = list(
        tbl_formula02.objects.filter(form=formula, is_deleted=False)
        .order_by('sequence_no')
        .values('material_code', 'concentration')
    )
    return JsonResponse({
        'form_id': formula.form_id,
        'index_no': formula.index_no or '-',
        'customer': formula.customer or '',
        'materials': materials
    }, safe=False)

def get_formulation_context(form_id=None):
    """Context for the Formulation page."""
    if form_id:
        form_data = get_formulation_details(form_id)
    else:
        max_id = tbl_formula01.objects.aggregate(Max('form_id'))['form_id__max'] or 0
        form_data = {
            'form_id': max_id + 1,
            'is_new': True
        }

    user_list = list(
        User.objects.filter(is_active=True)
        .exclude(first_name="")
        .annotate(full_name=Concat('first_name', Value(' '), 'last_name'))
        .values_list('full_name', flat=True)
        .distinct()
        .order_by('full_name')
    )
    
    return {
        'form_data': form_data,
        'formulation_records': get_formulation_list(),
        'matching_numbers': get_all_matching_numbers(),
        'users': user_list,
        'materials': cmf_records_services.get_raw_material_codes(),
        'customers': ["Masterbatch PH", "Generic Co."],
    }

def save_formulation(request):
    """Creates or updates a Formulation record and handles source tracking."""
    try:
        with transaction.atomic():
            data = request.POST
            form_id = data.get('form_id')
            is_new = data.get('is_new_flag') == 'true'
            current_time_str = timezone.now().strftime('%m/%d/%Y %I:%M %p')
            
            if not is_new and form_id:
                f = tbl_formula01.objects.get(pk=form_id)
                action_type = "Updated"
                log_message = f"Updated Formulation Entry: {form_id}"
                f.date_time = current_time_str
            else:
                f = tbl_formula01()
                if form_id:
                    f.form_id = form_id 
                action_type = "Saved"
                log_message = f"New Formulation Entry: {form_id}"
                f.date = timezone.now().date()
                f.date_time = None  

            # Field Mapping
            f.customer = data.get('customer')
            f.index_no = data.get('index_no')
            f.prod_code = data.get('product_code')
            f.prod_color = data.get('prod_color')
            f.total_concentration = data.get('total_concentration') or 0
            f.dosage = data.get('sum_of_concentration') or 0 # Visible Input
            f.ld = data.get('dosage') or 0                 # Dosage Input
            f.mix_time = data.get('mix_time')
            f.resin = data.get('resin')
            f.application = data.get('application')
            f.colormatch_no = data.get('cm_no')
            f.notes = data.get('notes')
            
            dt_str = data.get('colormatch_date')
            if dt_str:
                try:
                    f.colormatch_date = datetime.strptime(dt_str, '%m/%d/%Y').date()
                except ValueError:
                    pass
            
            f.save()

            # Handle Materials
            tbl_formula02.objects.filter(form=f).delete()
            materials_json = data.get('materials_data')
            if materials_json:
                materials = json.loads(materials_json)
                for i, mat in enumerate(materials):
                    tbl_formula02.objects.create(
                        form=f,
                        sequence_no=i + 1,
                        material_code=mat['material'],
                        concentration=mat['concentration']
                    )

            # Handle Metadata
            encode, _ = tbl_formula_encode.objects.get_or_create(form=f)
            encode.match_by = data.get('matched_by')
            if is_new:
                encode.encoded_by = data.get('encoded_by') or request.user.first_name
                encode.updated_by = None 
            else:
                encode.updated_by = request.user.first_name if request.user.is_authenticated else "System"
            encode.save()

            # Update Source Formula (MB or DC)
            source_pk = data.get('source_formula_pk')
            source_type = data.get('source_formula_type')
            if source_pk and source_type:
                if source_type == 'MB':
                    tbl_mb_extruder_formula.objects.filter(pk=source_pk).update(in_master_formula=True)
                elif source_type == 'DC':
                    tbl_dc_extruder_formula.objects.filter(pk=source_pk).update(in_master_formula=True)

            log_audit(request, action_type, log_message)
            cache.delete('formulation_records_list')
            return True, f.form_id
            
    except Exception as e:
        return False, str(e)

def formulation_lookup(request):
    """Lookup logic for Formulas by CM/RS No."""
    matching_no = request.GET.get('matching_no', '').strip()
    error = None
    mb_list = []
    dc_list = []
    
    parent = {'customer': '', 'resin_used': '', 'colorant_type': '', 'process': ''}
    color = ''

    if not matching_no:
        error = "No matching number provided."
    else:
        cmf = tbl_cmf.objects.filter(cm_no=matching_no).first()
        rs_records = tbl_rs.objects.filter(rs_no=matching_no) if not cmf else None

        if not cmf and not rs_records.exists():
            error = f'No CMF or RS record found for "{matching_no}".'
        else:
            if cmf:
                formula_info = tbl_cmf_formula.objects.filter(cm_no=cmf).first()
                parent['customer'] = formula_info.customer if formula_info else ""
                parent['colorant_type'] = cmf.colorant_type or ""
                resins = tbl_resins_selected.objects.filter(cm_no=cmf).values_list('resin_no__abbreviation', flat=True)
                parent['resin_used'] = ", ".join(filter(None, resins))
                processes = tbl_cmf_process02.objects.filter(cmf_formula_no=formula_info).values_list('process_no__name', flat=True)
                parent['process'] = ", ".join(filter(None, processes))
                mb_qs = tbl_mb_extruder_formula.objects.filter(cm_no=cmf).select_related('code')
                dc_qs = tbl_dc_extruder_formula.objects.filter(cm_no=cmf).select_related('code')
                color = cmf.in_code_no.color if cmf.in_code_no else (cmf.color_desc or '---')
            else:
                rs_ids = list(rs_records.values_list('id', flat=True))
                base_rs = rs_records.first()
                parent['customer'] = base_rs.customer or ""
                parent['colorant_type'] = base_rs.colorant_type or ""
                color = base_rs.primary_color or base_rs.color_desc or '---'
                resins = tbl_resins_selected.objects.filter(rs_no_id__in=rs_ids).values_list('resin_no__abbreviation', flat=True).distinct()
                parent['resin_used'] = ", ".join(filter(None, resins))
                processes = tbl_cmf_process02.objects.filter(rs_no_id__in=rs_ids).values_list('process_no__name', flat=True).distinct()
                parent['process'] = ", ".join(filter(None, processes))
                mb_qs = tbl_mb_extruder_formula.objects.filter(rs_no_id__in=rs_ids).select_related('code')
                dc_qs = tbl_dc_extruder_formula.objects.filter(rs_no_id__in=rs_ids).select_related('code')

            for f in mb_qs:
                ingredients = [{'material': ing.material, 'value': float(ing.value) if ing.value is not None else 0} for ing in tbl_mb_extruder_formula02.objects.filter(mb=f)]
                mb_list.append({
                    'header': f, 'pk': f.mb_no, 'ingredients': ingredients,
                    'sum_con': format(sum(item['value'] for item in ingredients), ".6f"),
                    'script_id': f'fml-ing-mb-{f.pk}'
                })

            for f in dc_qs:
                ingredients = [{'material': ing.material, 'value': float(ing.value) if ing.value is not None else 0} for ing in tbl_dc_extruder_formula02.objects.filter(dc=f)]
                dc_list.append({
                    'header': f, 'pk': f.dc_no, 'ingredients': ingredients,
                    'sum_con': format(sum(item['value'] for item in ingredients), ".6f"),
                    'script_id': f'fml-ing-dc-{f.pk}'
                })
    
    return render(request, "modal/master-formula/master_formula_lookup.html", {
        'matching_no': matching_no, 'error': error, 'color': color,
        'parent': parent, 'mb_formulas': mb_list, 'dc_formulas': dc_list,
    })