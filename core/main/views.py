from urllib import request

from django.core.cache import cache
from django.contrib.auth import authenticate, login, logout, get_user_model 
from django.contrib.auth.models import User
from django.shortcuts import redirect, render
from django.contrib import messages
from datetime import datetime

from main.services.save import mb_formula_save
from main.decorators import role_required
from main.models import tbl_cmf, tbl_cmf_formula, tbl_cmf_process02, tbl_cmf_process02, tbl_internal_color_code, tbl_resin, tbl_cmf_salesman, tbl_resins_selected

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
        try:
            saved_record = cmf_entry_save.save_cmf_complete_entry(request)
            messages.success(request, f"Successfully saved CMF No. {saved_record.cm_no}")
            cache.delete('cmf_records_list') 
            return redirect('cmf_entry')
        except Exception as e:
            messages.error(request, str(e))
            form_data = request.POST # Keep data to send back to template

    context = {
        "customers": ["Masterbatch PH", "Generic Co."],
        "salesman": tbl_cmf_salesman.objects.all().order_by('name'),
        "primary_color": tbl_internal_color_code.objects.all().order_by('color'),
        "resin": tbl_resin.objects.filter(is_deleted=False).order_by('abbreviation'),
        "form_data": form_data # This allows the HTML to keep user input
    }
    return render(request, "sidemenu/cmf/cmf_entry.html", context)

def cmf_rs_entry(request):
    return render(request, "sidemenu/cmf/rs_entry.html")


def cmf_mb_formula(request):
    form_data = {}
    
    if request.method == "POST":
        # ... (keep your existing POST saving logic) ...
        try:
            saved_record = mb_formula_save.save_mb_complete_formula(request)
            messages.success(request, f"Successfully saved MB Formula for CMF No. {saved_record.cm_no.cm_no}")
            cache.delete('cmf_records_list')
            return redirect('cmf_mb_formula')
        except Exception as e:
            messages.error(request, f"Error saving formula: {str(e)}")
            form_data = request.POST 

    else:
        cm_no = request.GET.get('no')
        if cm_no:
            cmf = tbl_cmf.objects.filter(cm_no=cm_no).first()
            if cmf:
                # 1. Fetch the CMF Formula Entry
                formula_info = tbl_cmf_formula.objects.filter(cm_no=cm_no).first()

                # 2. GET MULTIPLE RESINS (Joined by Comma)
                resins_list = tbl_resins_selected.objects.filter(
                    cm_no=cm_no
                ).values_list('resin_no__abbreviation', flat=True)
                resin_used_str = ", ".join(resins_list)

                # 3. GET PROCESS/APPLICATION (Based on your new ERD)
                # We filter tbl_cmf_process02 by the cm_no (via the formula FK) 
                # and grab the 'name' from the related tbl_cmf_process table
                processes = tbl_cmf_process02.objects.filter(
                    cmf_formula_no__cm_no=cm_no
                ).values_list('process_no__name', flat=True)
                
                application_str = ", ".join(processes)

                form_data = {
                    'cm_form_no': cm_no,
                    'customer': formula_info.customer if formula_info else "",
                    'resin_used': resin_used_str,
                    'dosage': formula_info.dosage if formula_info else "",
                    'finished_product': formula_info.finished_product if formula_info else "",
                    'color': cmf.in_code_no.color if cmf.in_code_no else "",
                    'application': application_str, # Updated logic
                }

    context = {
        "form_data": form_data 
    }
    return render(request, "sidemenu/cmf/formula_mb.html", context)


def cmf_dc_formula(request):
    return render(request, "sidemenu/cmf/formula_dc.html")


def cmf_pending_completed(request):
    return render(request, "sidemenu/cmf/pending_completed.html")


def feedback(request):
    return render(request, "sidemenu/feedback/feedback.html")


def audit_trail(request):
    return render(request, "sidemenu/audit_trail.html")