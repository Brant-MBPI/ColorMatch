from urllib import request

from django.core.cache import cache
from django.contrib.auth import authenticate, login, logout, get_user_model 
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from datetime import datetime

from main.services.save import mb_formula_save, dc_formula_save
from main.decorators import role_required
from main.models import (
    tbl_audit_trail, tbl_cmf, tbl_cmf_dates, tbl_cmf_formula, tbl_cmf_pending_completed, 
    tbl_cmf_process02, tbl_cmf_process02, tbl_cmf_specification02, tbl_dc_extruder_formula, 
    tbl_dc_extruder_formula02, tbl_internal_color_code, tbl_mb_extruder_formula, 
    tbl_mb_extruder_formula02, tbl_resin, tbl_cmf_salesman, tbl_resins_selected, 
    tbl_cmf_color_req, tbl_cmf_specification, tbl_cmf_process
)

from .services.cmf_records import cmf_records_services
from .services.save import cmf_entry_save
# Create your views here.
User = get_user_model()

def index(request):
    if request.user.is_authenticated:
        if request.user.role:
            return redirect('dashboard')
        else:
            return redirect('pending_role')
    else:
        return redirect('signin')

def pending_role(request):
    if request.user.is_authenticated and request.user.role:
        return redirect('dashboard')
    return render(request, 'login/pending-role.html')


def signin(request):
    next_url = request.GET.get('next', '') or request.POST.get('next', '')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect(next_url or 'dashboard')

        messages.error(request, "Incorrect username or password.")

    return render(request, 'login/signin.html', {'next': next_url})


def signup(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')

        errors = []
        if not all([first_name, last_name, username, email, password]):
            errors.append("All fields are required.")
        if password != confirm_password:
            errors.append("Passwords do not match.")
        if User.objects.filter(username=username).exists():
            errors.append("That username is already taken.")
        if User.objects.filter(email=email).exists():
            errors.append("That email is already registered.")

        if errors:
            for e in errors:
                messages.error(request, e)
            return render(request, 'login/signup.html')

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )
        login(request, user)
        return redirect('dashboard')

    return render(request, 'login/signup.html')


def signout(request):
    logout(request)
    return redirect('signin')

@role_required # This now handles both login AND role check
def dashboard(request):
    return render(request, "sidemenu/dashboard/dashboard.html")


def otherPage(request):
    return render(request, "sidemenu/other.html")


def cmf_records(request):
    all_records = cmf_records_services.get_all_records_combined()
    return render(request, "sidemenu/cmf/cmf_records.html", {
        "records": all_records,
    })

def cmf_entry(request):
    form_data = {}
    if request.method == "POST":
        original_cmf_no = request.POST.get('original_cmf_no', '').strip()
        try:
            if original_cmf_no:
                saved_record = cmf_entry_save.update_cmf_complete_entry(request, original_cmf_no)
                messages.success(request, f"Successfully updated CMF No. {saved_record.cm_no}")
            else:
                saved_record = cmf_entry_save.save_cmf_complete_entry(request)
                messages.success(request, f"Successfully saved CMF No. {saved_record.cm_no}")

            cache.delete('cmf_records_list')
            return redirect('cmf_entry')
        except Exception as e:
            messages.error(request, str(e))
            form_data = request.POST

    else:
        cm_no = request.GET.get('no')
        if cm_no:
            cmf = tbl_cmf.objects.filter(cm_no=cm_no).first()
            if cmf:
                dates = tbl_cmf_dates.objects.filter(cm_no=cmf).first()
                formula_info = tbl_cmf_formula.objects.filter(cm_no=cmf).first()
                color_req = tbl_cmf_color_req.objects.filter(cm_no=cmf).first()
        
                resin_ids = list(
                    tbl_resins_selected.objects.filter(cm_no=cmf).values_list('resin_no_id', flat=True)
                )
                process_names = list(
                    tbl_cmf_process02.objects.filter(cmf_formula_no=formula_info)
                    .values_list('process_no__name', flat=True)
                ) if formula_info else []
                spec_names = list(
                    tbl_cmf_specification02.objects.filter(cm_no=cmf)
                    .values_list('spec_no__name', flat=True)
                )

                form_data = {
                    'cmf_no': cmf.cm_no,
                    'customer': formula_info.customer if formula_info else "",

                    # DateField — needs strftime
                    'date_created': dates.form_made.strftime('%m/%d/%Y') if dates and dates.form_made else "",
                    'due_date': dates.due_date_lab.strftime('%m/%d/%Y') if dates and dates.due_date_lab else "",

                    # CharField — stored exactly as Flatpickr formatted it, pass through as-is
                    # (could be "ASAP" for required_date, or "MM/DD/YYYY, MM/DD/YYYY" for date_received)
                    'required_date': dates.date_required if dates else "",
                    'date_received': dates.date_received_lab if dates else "",

                    'matchType': cmf.matching_type,
                    'salesman': cmf.sm.name if cmf.sm else "",
                    'finished_product': formula_info.finished_product if formula_info else "",
                    'primary_color': str(cmf.in_code_no_id) if cmf.in_code_no_id else "",
                    'color_description': cmf.color_desc,
                    'colorReq': color_req.name if color_req else "",
                    'qty_resin_test': cmf.qty_resin_testing,
                    'customerResin': 'Y' if cmf.is_resin_provided else ('N' if cmf.is_resin_provided is False else ''),
                    'mi_customer_resin': cmf.mi_c_resin,
                    'sampleColorant': 'Y' if cmf.is_sample_available else ('N' if cmf.is_sample_available is False else ''),
                    'colorantType': cmf.colorant_type if cmf.colorant_type in ('MB', 'DC') else 'Other',
                    'colorantTypeOther': cmf.colorant_type if cmf.colorant_type not in ('MB', 'DC') else '',
                    'dosage': formula_info.dosage if formula_info else "",
                    'processing_temp': cmf.temperature,
                    'color_guide_return': 'Y' if cmf.is_guide_to_return else ('N' if cmf.is_guide_to_return is False else ''),
                    'is_low_cost': 'Y' if cmf.is_low_cost else ('N' if cmf.is_low_cost is False else ''),
                    'remarks': cmf.remarks,

                    # plain lists — NOT a QueryDict, template must use "in form_data.resin" (not .getlist.resin)
                    'resin': [str(rid) for rid in resin_ids],
                    'process': process_names,
                    'specification': spec_names,
                }

    context = {
        "customers": ["Masterbatch PH", "Generic Co."],
        "salesman": tbl_cmf_salesman.objects.all().order_by('name'),
        "primary_color": tbl_internal_color_code.objects.all().order_by('color'),
        "resin": tbl_resin.objects.filter(is_deleted=False).order_by('abbreviation'),
        "form_data": form_data
    }
    return render(request, "sidemenu/cmf/cmf_entry.html", context)

def cmf_rs_entry(request):
    return render(request, "sidemenu/cmf/rs_entry.html")


def cmf_record_detail(request, cm_no):
    # 1. Fetch Header Data
    cmf = get_object_or_404(tbl_cmf, cm_no=cm_no)
    formula_info = tbl_cmf_formula.objects.filter(cm_no=cm_no).first()
    pending_info = tbl_cmf_pending_completed.objects.filter(cm_no=cm_no).first()

    # 2. Fetch MB Formulas + Ingredients
    mb_list = []
    mb_qs = tbl_mb_extruder_formula.objects.filter(cm_no=cm_no).select_related('code')
    for f in mb_qs:
        ingredients = tbl_mb_extruder_formula02.objects.filter(mb=f)
        mb_list.append({'header': f, 'ingredients': ingredients})

    # 3. Fetch DC Formulas + Ingredients
    dc_list = []
    dc_qs = tbl_dc_extruder_formula.objects.filter(cm_no=cm_no).select_related('code')
    for f in dc_qs:
        ingredients = tbl_dc_extruder_formula02.objects.filter(dc=f)
        dc_list.append({'header': f, 'ingredients': ingredients})

    context = {
        'cmf': cmf,
        'formula_info': formula_info,
        'pending_info': pending_info,
        'mb_formulas': mb_list,
        'dc_formulas': dc_list,
    }
    # IMPORTANT: Use a partial template file
    return render(request, "modal/cmf-record/cmf_record_detail.html", context)

def cmf_mb_formula(request):
    form_data = {}
    ingredients = []
    colorant_mismatch = False

    if request.method == "POST":
        try:
            saved_record = mb_formula_save.save_mb_complete_formula(request)
            messages.success(request, f"Successfully saved MB Formula for CMF No. {saved_record.cm_no.cm_no}")
            cache.delete('cmf_records_list')
            return redirect('mb_formula')
        except Exception as e:
            messages.error(request, f"Error saving formula: {str(e)}")
            form_data = request.POST

    else:
        cm_no = request.GET.get('no')
        formula_id = request.GET.get('formula_id')

        if cm_no:
            cmf = tbl_cmf.objects.filter(cm_no=cm_no).first()
            if cmf:
                colorant_mismatch = cmf.colorant_type != "MB"

                formula_info = tbl_cmf_formula.objects.filter(cm_no=cm_no).first()

                resins_list = tbl_resins_selected.objects.filter(
                    cm_no=cm_no
                ).values_list('resin_no__abbreviation', flat=True)
                resin_used_str = ", ".join(resins_list)

                processes = tbl_cmf_process02.objects.filter(
                    cmf_formula_no__cm_no=cm_no
                ).values_list('process_no__name', flat=True)
                application_str = ", ".join(processes)

                # CMF-level defaults — always populated regardless of formula_id
                form_data = {
                    'cm_form_no': cm_no,
                    'customer': formula_info.customer if formula_info else "",
                    'resin_used': resin_used_str,
                    'dosage': formula_info.dosage if formula_info else "",
                    'finished_product': formula_info.finished_product if formula_info else "",
                    'color': cmf.in_code_no.color if cmf.in_code_no else "",
                    'application': application_str,
                }

                # --- Load a SPECIFIC historical formula, if one was clicked ---
                if formula_id:
                    header = tbl_mb_extruder_formula.objects.filter(pk=formula_id, cm_no=cmf).first()
                    if header:
                        form_data.update({
                            'formula_id': header.pk,
                            'date': header.date.strftime('%m/%d/%Y') if header.date else "",
                            'product': header.code.product_code if header.code else "",
                            'lot_number': header.lot_no or "",
                            'mixing_time': header.mixing_time or "",
                            'matched_by': header.matched_by or "",
                            'weighed_by': header.weighted_by or "",
                            'encoded_by': header.encoded_by or "",
                            'total_weight': header.total_weight,
                            'spectro_l': header.L,
                            'spectro_a': header.A,
                            'spectro_b': header.B,
                            'spectro_c': header.C,
                            'spectro_h': header.H,
                            'srgb_hex': header.html or "",
                            'cmyk_c': header.c,
                            'cmyk_m': header.m,
                            'cmyk_y': header.y,
                            'cmyk_k': header.k,
                        })

                        ingredients = list(
                            tbl_mb_extruder_formula02.objects.filter(mb=header)
                            .values('material', 'value', 'weight')
                        )
                        ingredients = ingredients + [{'material': '', 'value': '', 'weight': ''}] * (10 - len(ingredients))
                        ingredients = ingredients[:10]
                    else:
                        messages.error(request, f"Formula record not found for ID {formula_id}.")
                if not ingredients:
                    ingredients = [{'material': '', 'value': '', 'weight': ''}] * 10
    user_names = User.objects.filter(is_active=True).exclude(first_name="").values_list('first_name', flat=True).distinct().order_by('first_name')

    context = {
        "form_data": form_data,
        "materials": cmf_records_services.get_raw_material_codes(),
        "users": list(user_names),
        "colorant_mismatch": colorant_mismatch,
        "ingredients": ingredients,
    }
    return render(request, "sidemenu/cmf/formula_mb.html", context)


def cmf_dc_formula(request):
    form_data = {}
    ingredients = []
    colorant_mismatch = False

    if request.method == "POST":
        try:
            saved_record = dc_formula_save.save_dc_complete_formula(request)
            messages.success(request, f"Successfully saved DC Formula for CMF No. {saved_record.cm_no.cm_no}")
            cache.delete('cmf_records_list')
            return redirect('dc_formula')
        except Exception as e:
            messages.error(request, f"Error saving formula: {str(e)}")
            form_data = request.POST

    else:
        cm_no = request.GET.get('no')
        formula_id = request.GET.get('formula_id')

        if cm_no:
            cmf = tbl_cmf.objects.filter(cm_no=cm_no).first()
            if cmf:
                colorant_mismatch = cmf.colorant_type != "DC"

                formula_info = tbl_cmf_formula.objects.filter(cm_no=cm_no).first()

                resins_list = tbl_resins_selected.objects.filter(cm_no=cm_no).values_list('resin_no__abbreviation', flat=True)
                resin_str = ", ".join(resins_list)

                processes = tbl_cmf_process02.objects.filter(cmf_formula_no__cm_no=cm_no).values_list('process_no__name', flat=True)
                app_str = ", ".join(processes)

                form_data = {
                    'cm_form_no': cm_no,
                    'customer': formula_info.customer if formula_info else "",
                    'resin': resin_str,
                    'dosage': formula_info.dosage if formula_info else "",
                    'finished_product': formula_info.finished_product if formula_info else "",
                    'color': cmf.in_code_no.color if cmf.in_code_no else "",
                    'application': app_str,
                }

                if formula_id:
                    header = tbl_dc_extruder_formula.objects.filter(pk=formula_id, cm_no=cmf).first()
                    if header:
                        form_data.update({
                            'formula_id': header.pk,
                            'date_matched': header.date.strftime('%m/%d/%Y') if header.date else "",
                            'product_code': header.code.product_code if header.code else "",
                            'sample_size': header.sample_size or "",
                            'mixing_time': header.mixing_time or "",
                            'matched_by': header.matched_by or "",
                            'weighed_by': header.weighed_by or "",
                            'encoded_by': header.encoded_by or "",
                            'total_weight': header.total_weight,
                            'spectro_l': header.L,
                            'spectro_a': header.A,
                            'spectro_b': header.B,
                            'spectro_c': header.C,
                            'spectro_h': header.H,
                            'srgb_hex': header.html or "",
                            'cmyk_c': header.c,
                            'cmyk_m': header.m,
                            'cmyk_y': header.y,
                            'cmyk_k': header.k,
                        })

                        ingredients = list(
                            tbl_dc_extruder_formula02.objects.filter(dc=header)
                            .values('material', 'value', 'weight')
                        )
                        # Pad/truncate to exactly 10 rows so the template can loop plainly
                        ingredients = ingredients + [{'material': '', 'value': '', 'weight': ''}] * (10 - len(ingredients))
                        ingredients = ingredients[:10]
                    else:
                        messages.error(request, f"Formula record not found for ID {formula_id}.")
                if not ingredients:
                    ingredients = [{'material': '', 'value': '', 'weight': ''}] * 10

    user_names = User.objects.filter(is_active=True).exclude(first_name="").values_list('first_name', flat=True).distinct().order_by('first_name')

    context = {
        "form_data": form_data,
        "materials": cmf_records_services.get_raw_material_codes(),
        "users": list(user_names),
        "colorant_mismatch": colorant_mismatch,
        "ingredients": ingredients,
    }
    return render(request, "sidemenu/cmf/formula_dc.html", context)


def cmf_pending_completed(request):
    form_data = {}
    cm_no = request.GET.get('no')

    if cm_no:
        cmf = tbl_cmf.objects.filter(cm_no=cm_no).first()
        if cmf:
            dates = tbl_cmf_dates.objects.filter(cm_no=cmf).first()
            formula_info = tbl_cmf_formula.objects.filter(cm_no=cmf).first()

            form_data = {
                'cmf_no': cmf.cm_no,
                'customer': formula_info.customer if formula_info else "",

                # DateField — needs strftime
                'date_created': dates.form_made.strftime('%m/%d/%Y') if dates and dates.form_made else "",
                'due_date': dates.due_date_lab.strftime('%m/%d/%Y') if dates and dates.due_date_lab else "",

                # CharField — stored exactly as Flatpickr formatted it, pass through as-is
                'required_date': dates.date_required if dates else "",
                'date_received': dates.date_received_lab if dates else "",

                'finished_product': formula_info.finished_product if formula_info else "",
                'color_description': cmf.color_desc,
                'matchType': cmf.matching_type.upper() if cmf.matching_type else "",
                'salesman': cmf.sm.name if cmf.sm else "",
            }

    context = {
        "form_data": form_data,
    }
    return render(request, "sidemenu/cmf/pending_completed.html", context)

def feedback(request):
    return render(request, "sidemenu/feedback/feedback.html")


@role_required
def audit_trail(request):
    cache_key = 'audit_trail_records_list'
    records = cache.get(cache_key)

    if records is None:
        # We use list() to evaluate the QuerySet immediately 
        # so the actual data is stored in the cache.
        records = list(
            tbl_audit_trail.objects.all()
            .select_related('user__role')
            .order_by('-timestamp')
        )
        # Store for 24 hours (86400 seconds) or until cache.delete is called
        cache.set(cache_key, records, 86400)

    context = {
        "records": records,
        "record_count": len(records),
    }
    return render(request, "sidemenu/audit_trail.html", context)