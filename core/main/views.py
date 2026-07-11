from urllib import request

from django.shortcuts import render
from django.http import HttpResponse

from main.models import tbl_internal_color_code, tbl_resin

from .services import cmf_records_services
# Create your views here.


def index(request):
    return render(request, "base.html")


def login(request):
    return render(request, "login/login.html")


def signup(request):
    return render(request, "login/signup.html")


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