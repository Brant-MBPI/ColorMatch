from django.core.cache import cache
from django.db.models.functions import Concat
from django.utils import timezone
import json
from datetime import datetime
from django.db import transaction
from django.http import JsonResponse
from django.db.models import Q, Max, Value
from django.shortcuts import render
from main.utils.log_audit_trail import log_audit
from main.services.cmf_records import cmf_records_services
from main.models import (
    tbl_cmf_formula, tbl_cmf_process02, tbl_dc_extruder_formula, tbl_dc_extruder_formula02, 
    tbl_master_formula, tbl_master_formula_info, tbl_master_formula_encode, 
    tbl_cmf, tbl_mb_extruder_formula, tbl_mb_extruder_formula02, tbl_resins_selected, tbl_rs
)
from django.contrib.auth import get_user_model 
User = get_user_model()

CACHE_TIMEOUT = 3600  # 1 hour

# --- 1. DATA RETRIEVAL (FOR ENTRY/EDIT) ---

def get_master_formula_details(form_id):
    """Fetches full details for a single master formula (Used when editing)."""
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
        'total_concentration': format(formula.total_concentration or 0, ".6f"),
        'sum_of_concentration': format(formula.dosage or 0, ".6f"),
        'dosage': formula.ld or '',
        'mix_time': formula.mix_time or '',
        'resin': formula.resin or '',
        'application': formula.application or '',
        'cm_no': formula.cm_no or '',
        'colormatch_date': formula.colormatch_date.strftime('%m/%d/%Y') if formula.colormatch_date else '',
        'notes': formula.notes or '',
        'html_code_hex': formula.html_code_hex or '',
        'cyan': formula.cyan or '',
        'magenta': formula.magenta or '',
        'yellow': formula.yellow or '',
        'black': formula.black or '',
        'updated_by': encode.updated_by if encode else '',
        'updated_time': formula.date_modified or '',
        'matched_by': encode.match_by if encode else '',
        'encoded_by': encode.encoded_by if encode else '',
        'materials': materials,
    }

def get_all_matching_numbers():
    """Fetches unique CM/RS numbers for the TomSelect dropdown (Cached)."""
    nos = cache.get('matching_numbers_list')
    if not nos:
        cmf_nos = list(tbl_cmf.objects.exclude(cm_no__isnull=True).exclude(cm_no='').values_list('cm_no', flat=True))
        rs_nos = list(tbl_rs.objects.exclude(rs_no__isnull=True).exclude(rs_no='').values_list('rs_no', flat=True))
        nos = sorted(list(set(cmf_nos + rs_nos)))
        cache.set('matching_numbers_list', nos, CACHE_TIMEOUT)
    return nos

def get_master_formula_context(form_id=None):
    """Context for the Master Formula page. Removed the 17k record list."""
    if form_id:
        form_data = get_master_formula_details(form_id)
    else:
        max_id = tbl_master_formula.objects.aggregate(Max('form_id'))['form_id__max'] or 0
        form_data = {'form_id': max_id + 1, 'is_new': True}

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
        'matching_numbers': get_all_matching_numbers(),
        'users': user_list,
        'materials': cmf_records_services.get_raw_material_codes(),
        'customers': ["Masterbatch PH", "Generic Co."],
    }

# --- 2. DATA TABLES (JSON ENDPOINTS) ---

def get_master_formula_records_json(request):
    """Server-side DataTables logic for Master Formula records (High Performance)."""
    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = request.GET.get('length', 1000) 
    
    if length == '-1':
        length = tbl_master_formula.objects.filter(is_deleted=False).count()
    else:
        length = int(length)

    search_value = request.GET.get('search[value]', '').strip()
    queryset = tbl_master_formula.objects.filter(is_deleted=False)
    total_records = queryset.count()

    if search_value:
        queryset = queryset.filter(
            Q(form_id__icontains=search_value) |
            Q(index_no__icontains=search_value) |
            Q(customer__icontains=search_value) |
            Q(product_code__icontains=search_value) |
            Q(prod_color__icontains=search_value)
        )

    # Ordering mapping
    order_column_index = request.GET.get('order[0][column]')
    order_dir = request.GET.get('order[0][dir]')
    column_mapping = {
        '0': 'form_id', '1': 'index_no', '2': 'customer', 
        '3': 'product_code', '4': 'prod_color', 
        '5': 'total_concentration', '6': 'ld'
    }
    
    order_field = column_mapping.get(order_column_index, '-form_id')
    if order_dir == 'desc' and not order_field.startswith('-'):
        order_field = f"-{order_field}"
    
    queryset = queryset.order_by(order_field)
    filtered_records = queryset.count()
    queryset = queryset[start:start + length]

    data = [{
        "form_id": row.form_id,
        "index_no": row.index_no or "-",
        "customer": row.customer or "-",
        "product_code": row.product_code or "-",
        "prod_color": row.prod_color or "-",
        "total_concentration": format(row.total_concentration or 0, ".6f"),
        "ld": format(row.ld or 0, ".6f"),
    } for row in queryset]

    return JsonResponse({
        "draw": draw,
        "recordsTotal": total_records,
        "recordsFiltered": filtered_records,
        "data": data,
    })

def master_formula_materials_json(request, form_id):
    """API for the Material Breakdown side-panel."""
    formula = tbl_master_formula.objects.filter(pk=form_id).first()
    if not formula:
        return JsonResponse({'error': 'Not found'}, status=404)
    
    materials = list(tbl_master_formula_info.objects.filter(form=formula, is_deleted=False)
                     .order_by('sequence_no').values('material_code', 'concentration'))
    
    return JsonResponse({
        'form_id': formula.form_id,
        'index_no': formula.index_no or '-',
        'customer': formula.customer or '',
        'materials': materials
    })

# --- 3. PERSISTENCE (SAVE / LOOKUP) ---

def save_master_formula(request):
    """Handles creating or updating a Master Formula."""
    try:
        with transaction.atomic():
            data = request.POST
            form_id = data.get('form_id')
            is_new = data.get('is_new_flag') == 'true'
            current_time_str = timezone.now().strftime('%m/%d/%Y %I:%M %p')
            
            if not is_new and form_id:
                mf = tbl_master_formula.objects.get(pk=form_id)
                action_type, log_message = "Updated", f"Updated Master Formula Entry: {form_id}"
                mf.date_modified = current_time_str
            else:
                mf = tbl_master_formula()
                if form_id: mf.form_id = form_id 
                action_type, log_message = "Saved", f"New Master Formula Entry: {form_id}"
                mf.date = timezone.now().date()
                mf.date_modified = None  

            # Field Mapping
            mf.customer = data.get('customer')
            mf.index_no = data.get('index_no')
            mf.product_code = data.get('product_code')
            mf.prod_color = data.get('prod_color')
            mf.total_concentration = data.get('total_concentration') or 0
            mf.dosage = data.get('sum_of_concentration') or 0
            mf.ld = data.get('dosage') or 0
            mf.mix_time, mf.resin, mf.application, mf.cm_no = data.get('mix_time'), data.get('resin'), data.get('application'), data.get('cm_no')
            mf.notes, mf.html_code_hex = data.get('notes'), data.get('html_code_hex')
            mf.cyan, mf.magenta, mf.yellow, mf.black = data.get('cyan') or None, data.get('magenta') or None, data.get('yellow') or None, data.get('black') or None
            
            dt_str = data.get('colormatch_date')
            if dt_str:
                try: mf.colormatch_date = datetime.strptime(dt_str, '%m/%d/%Y').date()
                except: pass
            mf.save()

            # Materials
            tbl_master_formula_info.objects.filter(form=mf).delete()
            materials_json = data.get('materials_data')
            if materials_json:
                for i, mat in enumerate(json.loads(materials_json)):
                    tbl_master_formula_info.objects.create(form=mf, sequence_no=i+1, material_code=mat['material'], concentration=mat['concentration'])

            # Metadata
            encode, _ = tbl_master_formula_encode.objects.get_or_create(form=mf)
            encode.match_by = data.get('matched_by')
            if is_new:
                encode.encoded_by, encode.updated_by = (data.get('encoded_by') or request.user.first_name), None
            else:
                encode.updated_by = request.user.first_name if request.user.is_authenticated else "System"
            encode.save()

            # Update Source Formula
            source_pk, source_type = data.get('source_formula_pk'), data.get('source_formula_type')
            if source_pk and source_type:
                model = tbl_mb_extruder_formula if source_type == 'MB' else tbl_dc_extruder_formula
                model.objects.filter(pk=source_pk).update(in_master_formula=True)

            log_audit(request, action_type, log_message)
            return True, mf.form_id
    except Exception as e:
        return False, str(e)

def master_formula_lookup(request):
    """Lookup logic for searching CM/RS records to import into Entry tab."""
    matching_no = request.GET.get('matching_no', '').strip()
    error, mb_list, dc_list, color = None, [], [], ''
    parent = {'customer': '', 'resin_used': '', 'colorant_type': '', 'process': ''}

    if not matching_no:
        error = "No matching number provided."
    else:
        cmf = tbl_cmf.objects.filter(cm_no=matching_no).first()
        rs_records = tbl_rs.objects.filter(rs_no=matching_no) if not cmf else None

        if not cmf and (not rs_records or not rs_records.exists()):
            error = f'No records found for "{matching_no}".'
        else:
            if cmf:
                formula_info = tbl_cmf_formula.objects.filter(cm_no=cmf).first()
                parent.update({'customer': formula_info.customer if formula_info else "", 'colorant_type': cmf.colorant_type or ""})
                parent['resin_used'] = ", ".join(tbl_resins_selected.objects.filter(cm_no=cmf).values_list('resin_no__abbreviation', flat=True))
                parent['process'] = ", ".join(tbl_cmf_process02.objects.filter(cmf_formula_no=formula_info).values_list('process_no__name', flat=True))
                mb_qs, dc_qs = tbl_mb_extruder_formula.objects.filter(cm_no=cmf).select_related('code'), tbl_dc_extruder_formula.objects.filter(cm_no=cmf).select_related('code')
                color = cmf.in_code_no.color if cmf.in_code_no else (cmf.color_desc or '---')
            else:
                rs_ids = list(rs_records.values_list('id', flat=True))
                base_rs = rs_records.first()
                parent.update({'customer': base_rs.customer or "", 'colorant_type': base_rs.colorant_type or ""})
                parent['resin_used'] = ", ".join(tbl_resins_selected.objects.filter(rs_no_id__in=rs_ids).values_list('resin_no__abbreviation', flat=True).distinct())
                parent['process'] = ", ".join(tbl_cmf_process02.objects.filter(rs_no_id__in=rs_ids).values_list('process_no__name', flat=True).distinct())
                mb_qs, dc_qs = tbl_mb_extruder_formula.objects.filter(rs_no_id__in=rs_ids).select_related('code'), tbl_dc_extruder_formula.objects.filter(rs_no_id__in=rs_ids).select_related('code')
                color = base_rs.primary_color or base_rs.color_desc or '---'

            for qs, target, ftype in [(mb_qs, mb_list, 'MB'), (dc_qs, dc_list, 'DC')]:
                for f in qs:
                    # Determine ingredients based on type
                    ing_model = tbl_mb_extruder_formula02 if ftype == 'MB' else tbl_dc_extruder_formula02
                    filter_key = {'mb': f} if ftype == 'MB' else {'dc': f}
                    ingredients = [{'material': i.material, 'value': float(i.value or 0)} for i in ing_model.objects.filter(**filter_key)]
                    target.append({
                        'header': f, 'pk': f.pk, 'ingredients': ingredients,
                        'sum_con': format(sum(item['value'] for item in ingredients), ".6f"),
                        'script_id': f'mf-ing-{ftype.lower()}-{f.pk}'
                    })

    return render(request, "modal/master-formula/master_formula_lookup.html", {
        'matching_no': matching_no, 'error': error, 'color': color, 'parent': parent,
        'mb_formulas': mb_list, 'dc_formulas': dc_list
    })