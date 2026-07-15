from urllib import request

from django.contrib.auth import authenticate, login, logout, get_user_model 
from django.contrib.auth.models import User
from django.shortcuts import redirect, render
from django.contrib import messages
from datetime import datetime

from main.decorators import role_required
from main.models import tbl_internal_color_code, tbl_resin

from .services import cmf_records_services
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
    if request.method == "POST":
        # 1. Helper function for Date Conversion (MM/DD/YYYY -> YYYY-MM-DD)
        def parse_dt(date_str):
            if not date_str: return None
            try:
                return datetime.strptime(date_str, '%m/%d/%Y').strftime('%Y-%m-%d')
            except ValueError:
                return date_str # Return as is if it's "ASAP" or invalid

        # 2. Extract General Information
        cmf_no = request.POST.get('cmf_no')
        customer = request.POST.get('customer')
        date_created = parse_dt(request.POST.get('date_created'))
        required_date = request.POST.get('required_date') # Might be "ASAP"
        date_received = request.POST.get('date_received') # Multiple dates might come as string
        due_date = parse_dt(request.POST.get('due_date'))
        match_type = request.POST.get('matchType')
        salesman = request.POST.get('salesman')
        finished_product = request.POST.get('finished_product')
        primary_color_id = request.POST.get('primary_color')
        description = request.POST.get('color_description')

        # 3. Handle Color Requirement (Radio + Other Text)
        color_req = request.POST.get('colorReq')
        if color_req == "other":
            color_req = request.POST.get('colorReq_other')

        # 4. Handle Resin (Many-to-Many select)
        selected_resins = request.POST.getlist('resin') 

        # 5. Handle Process (Checkboxes + Other Text)
        processes = request.POST.getlist('process')
        if "others" in processes:
            # Remove "others" keyword and add the actual text from the input
            processes.remove("others")
            other_p = request.POST.get('otherProcess')
            if other_p: processes.append(other_p)
        process_string = ", ".join(processes) # Store as comma-separated string

        # 6. Technical Specs
        qty_resin_test = request.POST.get('qty_resin_test')
        customer_resin = request.POST.get('customerResin') # Y/N
        mi_resin = request.POST.get('mi_customer_resin')
        sample_available = request.POST.get('sampleColorant') # Y/N

        # 7. Colorant Type (Radio + Other Text)
        colorant_type = request.POST.get('colorantType')
        if colorant_type == "Other":
            colorant_type = request.POST.get('colorantTypeOther')

        dosage = request.POST.get('dosage')
        processing_temp = request.POST.get('processing_temp')

        # 8. Other Specifications (Checkboxes + Other Text)
        specs = request.POST.getlist('specification')
        if "Others" in specs:
            specs.remove("Others")
            other_s = request.POST.get('specificationOther')
            if other_s: specs.append(other_s)
        specs_string = ", ".join(specs)

        color_guide_return = request.POST.get('color_guide_return') # Y/N
        is_low_cost = request.POST.get('is_low_cost') # Y/N
        remarks = request.POST.get('remarks')
        product_code = request.POST.get('product_code')

        # 9. SAVE TO DATABASE
        try:
            # Create the main record
            # Note: I am assuming field names in your model match these variables
            new_entry = tbl_cmf_entry.objects.create(
                cmf_no=cmf_no,
                customer=customer,
                date_created=date_created,
                required_date=required_date,
                date_received=date_received,
                due_date=due_date,
                match_type=match_type,
                salesman=salesman,
                finished_product=finished_product,
                primary_color_id=primary_color_id, # ForeignKey ID
                description=description,
                color_requirement=color_req,
                process=process_string,
                qty_resin_test=qty_resin_test,
                customer_resin_provided=customer_resin,
                mi_customer_resin=mi_resin,
                sample_colorant_available=sample_available,
                colorant_type=colorant_type,
                dosage=dosage,
                processing_temp=processing_temp,
                other_specifications=specs_string,
                color_guide_return=color_guide_return,
                is_low_cost=is_low_cost,
                remarks=remarks,
                product_code=product_code,
                created_by=request.user
            )

            # Link the Many-to-Many resins
            if selected_resins:
                new_entry.resins.set(selected_resins)

            messages.success(request, f"Entry {cmf_no} saved successfully!")
            return redirect('cmf_entry') 

        except Exception as e:
            print(f"Error: {e}") # View this in your terminal
            messages.error(request, "Error saving to database. Check console.")

    # --- GET DATA FOR PAGE LOAD ---
    customers = ["Masterbatch PH", "Generic Co."]
    salesman = ["Brant Jan Abillanoza", "Francis Candedlaria"]
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