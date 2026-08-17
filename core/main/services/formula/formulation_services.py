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
    tbl_formula01, tbl_formula02, tbl_formula_encode,
    tbl_cmf, tbl_rs, tbl_resins_selected, tbl_cmf_process02, tbl_cmf_formula,
    tbl_mb_extruder_formula, tbl_mb_extruder_formula02,
    tbl_dc_extruder_formula, tbl_dc_extruder_materials, tbl_dc_extruder_version
)
from django.contrib.auth import get_user_model 
User = get_user_model()

CACHE_TIMEOUT = 3600  # 1 hour

# --- 1. DATA RETRIEVAL (FOR ENTRY/EDIT) ---

def get_formulation_details(form_id):
    """Fetches full details for a single formulation (Used when editing)."""
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
        'total_concentration': format(f.total_concentration or 0, ".6f"),
        'sum_of_concentration': format(f.dosage or 0, ".6f"), 
        'dosage': format(f.ld or 0, ".6f"),
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

def get_formulation_context(form_id=None):
    """Context for the Formulation page. 17k list removed to save memory."""
    if form_id:
        form_data = get_formulation_details(form_id)
    else:
        max_id = tbl_formula01.objects.aggregate(Max('form_id'))['form_id__max'] or 0
        form_data = {'form_id': max_id + 1, 'is_new': True}

    user_list = list(
        User.objects.filter(is_active=True)
        .exclude(first_name="")
        .annotate(full_name=Concat('first_name', Value(' '), 'last_name'))
        .values_list('full_name', flat=True)
        .distinct()
        .order_by('full_name')
    )
    
    from .master_formula_services import get_all_matching_numbers

    return {
        'form_data': form_data,
        'matching_numbers': get_all_matching_numbers(),
        'users': user_list,
        'materials': cmf_records_services.get_raw_material_codes(),
        'customers': ["Masterbatch PH", "Generic Co."],
    }

# --- 2. DATA TABLES (HIGH PERFORMANCE JSON) ---

def get_formulation_records_json(request):
    """Server-side DataTables logic for 17,000+ Formulation records."""
    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 1000))
    
    search_value = request.GET.get('search[value]', '').strip()
    queryset = tbl_formula01.objects.filter(is_deleted=False)
    total_records = queryset.count()

    if search_value:
        queryset = queryset.filter(
            Q(form_id__icontains=search_value) |
            Q(index_no__icontains=search_value) |
            Q(customer__icontains=search_value) |
            Q(prod_code__icontains=search_value) |
            Q(prod_color__icontains=search_value)
        )

    order_col = request.GET.get('order[0][column]', '0')
    order_dir = request.GET.get('order[0][dir]', 'desc')
    mapping = {'0': 'form_id', '1': 'index_no', '2': 'customer', '3': 'prod_code', '4': 'prod_color'}
    sort_field = mapping.get(order_col, 'form_id')
    queryset = queryset.order_by(f"{'-' if order_dir == 'desc' else ''}{sort_field}")

    filtered_records = queryset.count()
    queryset = queryset[start:start + length]

    data = [{
        "form_id": row.form_id,
        "index_no": row.index_no or "-",
        "customer": row.customer or "-",
        "product_code": row.prod_code or "-",
        "prod_color": row.prod_color or "-",
        "total_concentration": format(row.total_concentration or 0, ".6f"),
        "ld": format(row.ld or 0, ".6f"),
    } for row in queryset]

    return JsonResponse({"draw": draw, "recordsTotal": total_records, "recordsFiltered": filtered_records, "data": data})

def formulation_materials_json(request, form_id):
    """API for the Side-Panel Material breakdown."""
    formula = tbl_formula01.objects.filter(pk=form_id).first()
    if not formula:
        return JsonResponse({'error': 'Not found'}, status=404)
    
    materials = list(tbl_formula02.objects.filter(form=formula, is_deleted=False)
                     .order_by('sequence_no').values('material_code', 'concentration'))
    
    return JsonResponse({
        'form_id': formula.form_id,
        'index_no': formula.index_no or '-',
        'customer': formula.customer or '',
        'materials': materials
    })

# --- 3. SAVE AND LOOKUP ---

def save_formulation(request):
    """Handles creating or updating a Formulation record with detailed Audit Trail."""
    try:
        with transaction.atomic():
            data = request.POST
            form_id = data.get('form_id')
            is_new = data.get('is_new_flag') == 'true'
            current_time_str = timezone.now().strftime('%m/%d/%Y %I:%M %p')
            
            diff_logs = []

            # 1. Capture Original Data if Updating
            if not is_new and form_id:
                f = tbl_formula01.objects.get(pk=form_id)
                action_type = "Updated"
                
                # Check Technical Field Changes
                # POST Key -> (Model Attribute, Display Label)
                field_map = {
                    'customer': ('customer', 'Customer'),
                    'index_no': ('index_no', 'Index #'),
                    'product_code': ('prod_code', 'Product Code'),
                    'prod_color': ('prod_color', 'Color'),
                    'sum_of_concentration': ('dosage', 'Sum of Con'),
                    'dosage': ('ld', 'Dosage'),
                    'mix_time': ('mix_time', 'Mixing Time'),
                    'resin': ('resin', 'Resin'),
                    'application': ('application', 'Application'),
                    'notes': ('notes', 'Notes'),
                    'cm_no': ('colormatch_no', 'CM Form #'),
                }

                for post_key, (model_attr, label) in field_map.items():
                    old_val = str(getattr(f, model_attr) or '').strip()
                    new_val = str(data.get(post_key) or '').strip()
                    if old_val != new_val:
                        diff_logs.append(f"{label}: {old_val} -> {new_val}")

                # Check for Material Changes
                old_mats = list(tbl_formula02.objects.filter(form=f).values_list('material_code', flat=True))
                new_mats_raw = data.get('materials_data')
                if new_mats_raw:
                    new_mats = [m['material'] for m in json.loads(new_mats_raw)]
                    if set(old_mats) != set(new_mats):
                        diff_logs.append("Material Breakdown updated")

                f.date_time = current_time_str
            else:
                f = tbl_formula01()
                if form_id: f.form_id = form_id 
                action_type = "Saved"
                f.date = timezone.now().date()
                f.date_time = None  

            # 2. Map and Save Fields
            f.customer = data.get('customer')
            f.index_no = data.get('index_no')
            f.prod_code = data.get('product_code')
            f.prod_color = data.get('prod_color')
            f.total_concentration = data.get('total_concentration') or 0
            f.dosage = data.get('sum_of_concentration') or 0
            f.ld = data.get('dosage') or 0
            f.mix_time, f.resin, f.application, f.colormatch_no = data.get('mix_time'), data.get('resin'), data.get('application'), data.get('cm_no')
            f.notes = data.get('notes')
            
            dt_str = data.get('colormatch_date')
            if dt_str:
                try: f.colormatch_date = datetime.strptime(dt_str, '%m/%d/%Y').date()
                except: pass
            f.save()

            # 3. Handle Materials
            tbl_formula02.objects.filter(form=f).delete()
            materials_json = data.get('materials_data')
            if materials_json:
                for i, mat in enumerate(json.loads(materials_json)):
                    tbl_formula02.objects.create(
                        form=f, sequence_no=i+1, 
                        material_code=mat['material'], 
                        concentration=mat['concentration']
                    )

            # 4. Metadata
            encode, _ = tbl_formula_encode.objects.get_or_create(form=f)
            encode.match_by = data.get('matched_by')
            if is_new:
                encode.encoded_by, encode.updated_by = (data.get('encoded_by') or request.user.first_name), None
            else:
                encode.updated_by = request.user.first_name if request.user.is_authenticated else "System"
            encode.save()

            # 5. Update Source Formula Reference
            source_pk, source_type = data.get('source_formula_pk'), data.get('source_formula_type')
            if source_pk and source_type:
                model = tbl_mb_extruder_formula if source_type == 'MB' else tbl_dc_extruder_formula
                model.objects.filter(pk=source_pk).update(in_master_formula=True)

            # 6. Audit Trail Logging
            if is_new:
                log_message = f"New Formulation Entry: #{f.form_id}"
            else:
                details = ", ".join(diff_logs) if diff_logs else "No technical changes"
                log_message = f"Formulation #{f.form_id}. Changes: {details}"

            log_audit(request, action_type, log_message)
            cache.delete('formulation_records_list')
            return True, f.form_id
            
    except Exception as e:
        return False, str(e)

def formulation_lookup(request):
    """Lookup logic for searching CM/RS records. Returns the LATEST Trial for DC formulas."""
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
                mb_qs = tbl_mb_extruder_formula.objects.filter(cm_no=cmf).select_related('code')
                dc_qs = tbl_dc_extruder_formula.objects.filter(cm_no=cmf).select_related('code')
                color = cmf.in_code_no.color if cmf.in_code_no else (cmf.color_desc or '---')
            else:
                rs_ids = list(rs_records.values_list('id', flat=True))
                base_rs = rs_records.first()
                parent.update({'customer': base_rs.customer or "", 'colorant_type': base_rs.colorant_type or ""})
                parent['resin_used'] = ", ".join(tbl_resins_selected.objects.filter(rs_no_id__in=rs_ids).values_list('resin_no__abbreviation', flat=True).distinct())
                parent['process'] = ", ".join(tbl_cmf_process02.objects.filter(rs_no_id__in=rs_ids).values_list('process_no__name', flat=True).distinct())
                mb_qs = tbl_mb_extruder_formula.objects.filter(rs_no_id__in=rs_ids).select_related('code')
                dc_qs = tbl_dc_extruder_formula.objects.filter(rs_no_id__in=rs_ids).select_related('code')
                color = base_rs.primary_color or base_rs.color_desc or '---'

            # PROCESS MB (Masterbatch)
            for f in mb_qs:
                ingredients = [{'material': i.material, 'value': float(i.value or 0)} 
                               for i in tbl_mb_extruder_formula02.objects.filter(mb=f)]
                mb_list.append({
                    'header': f, 'pk': f.pk, 'ingredients': ingredients,
                    'sum_con': format(sum(item['value'] for item in ingredients), ".6f"),
                    'script_id': f'fml-ing-mb-{f.pk}'
                })

            # PROCESS DC (Dry Color - Pulling Latest Version Only)
            for f in dc_qs:
                # 1. Find the highest version number recorded for this formula
                max_v = tbl_dc_extruder_version.objects.filter(material__dc=f).aggregate(Max('version_no'))['version_no__max']
                
                if max_v:
                    # 2. Fetch all materials and their specific values for that version
                    version_rows = tbl_dc_extruder_version.objects.filter(
                        material__dc=f, 
                        version_no=max_v
                    ).select_related('material')

                    ingredients = [
                        {'material': v.material.material, 'value': float(v.value or 0)}
                        for v in version_rows if v.value is not None
                    ]

                    dc_list.append({
                        'header': f, 
                        'pk': f.pk, 
                        'version': max_v,
                        'ingredients': ingredients,
                        'sum_con': format(sum(item['value'] for item in ingredients), ".6f"),
                        'script_id': f'fml-ing-dc-{f.pk}'
                    })

    return render(request, "modal/master-formula/master_formula_lookup.html", {
        'matching_no': matching_no, 'error': error, 'color': color, 'parent': parent,
        'mb_formulas': mb_list, 'dc_formulas': dc_list
    })