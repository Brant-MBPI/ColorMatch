from urllib import request

from django.contrib.auth import authenticate, login, logout, get_user_model 
from django.contrib.auth.models import User
from django.shortcuts import redirect, render
from django.contrib import messages

from main.models import tbl_internal_color_code, tbl_resin

from .services import cmf_records_services
# Create your views here.
User = get_user_model()

def index(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    else:
        return redirect('signin')


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


def dashboard(request):
    return render(request, "sidemenu/dashboard/dashboard.html")


def otherPage(request):
    return render(request, "sidemenu/other.html")


def cmf_records(request):
    mode = request.GET.get('mode', 'cmf')
    show_completed = request.GET.get('completed', '1') == '1'
    show_pending = request.GET.get('pending', '1') == '1'

    records = cmf_records_services.get_filtered_records(mode, show_completed, show_pending)
    active_cols = cmf_records_services.get_active_columns(show_completed, show_pending)

    context = {
        'records': records,
        'active_cols': active_cols,
        'col_no_label': "RS No." if mode == 'rs' else "CMF No.",
        'mode': mode,
        'show_completed': show_completed,
        'show_pending': show_pending,
    }

    return render(request, "sidemenu/cmf/cmf_records.html", context)


def cmf_entry(request):
    customers = [
        "Masterbatch PH",
        "Generic Co.",
    ]
    salesman = [
        "Brant Jan Abillanoza",
        "Francis Candedlaria",
    ]
    primary_color = tbl_internal_color_code.objects.all().order_by('color')

    resins_query = tbl_resin.objects.filter(is_deleted=False).order_by('abbreviation')

    return render(request, "sidemenu/cmf/cmf_entry.html", {
        "customers": customers,
        "salesman": salesman,
        "primary_color": primary_color,
        "resin": resins_query,
    })


def cmf_rs_entry(request):
    return render(request, "sidemenu/cmf/rs_entry.html")


def cmf_mb_formula(request):
    return render(request, "sidemenu/cmf/formula_mb.html")


def cmf_dc_formula(request):
    return render(request, "sidemenu/cmf/formula_dc.html")


def cmf_pending_completed(request):
    return render(request, "sidemenu/cmf/pending_completed.html")


def feedback(request):
    return render(request, "sidemenu/feedback/feedback.html")


def audit_trail(request):
    return render(request, "sidemenu/audit_trail.html")