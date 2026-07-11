from django.db import migrations

def populate_everything(apps, schema_editor):
    # Fetch models
    Role = apps.get_model('main', 'tbl_role')
    AccessPoint = apps.get_model('main', 'tbl_access_point')
    Permission = apps.get_model('main', 'tbl_role_permissions')
    CodingMat = apps.get_model('main', 'tbl_coding_materials')
    Resin = apps.get_model('main', 'tbl_resin') # Corrected to singular
    InternalColor = apps.get_model('main', 'tbl_internal_color_code')

    # 1. THE COMPLETE ROLES LIST (6 Roles)
    roles_list = [
        ('Information Technology', 'ADMIN'),
        ('Production', 'HEAD'),
        ('Production', 'STAFF'),
        ('Laboratory', 'HEAD'),
        ('Laboratory', 'STAFF'),
        ('Sales', 'SALES')
    ]
    for dept, role_name in roles_list:
        Role.objects.get_or_create(department=dept, role=role_name)

    # 2. THE COMPLETE ACCESS LIST (10 Points)
    access_list = [
        'Dashboard', 'CMF Records', 'CMF Entry', 'RS Entry', 
        'MB Formula', 'DC Formula', 'Pending Completed', 
        'Feedback', 'Audit Trail', 'Permission Access'
    ]
    for name in access_list:
        AccessPoint.objects.get_or_create(access_name=name)

    # 3. CODING MATERIALS
    coding_data = [
        ('D', 'Pigment'), ('T', 'Metallic'), ('P', 'Pearlized'), 
        ('M', 'Marble'), ('L', 'LINER')
    ]
    for c_code, c_name in coding_data:
        CodingMat.objects.get_or_create(code=c_code, name=c_name)

    # 4. RESINS (Complete list)
    resin_data = [
        ('PP', 'P'), ('PE', 'E'), ('PVC', 'V'), ('AS', 'S'), ('ABS', 'A'),
        ('GPPS', 'G'), ('HIPS', 'H'), ('UNIVERSAL', 'U'), ('PET', 'T'),
        ('EPS', 'X'), ('POLYCARBONATE', 'C'), ('EVA', 'EV'), ('NYLON', 'N')
    ]
    for abbr, r_code in resin_data:
        Resin.objects.get_or_create(abbreviation=abbr, code=r_code)

    # 5. INTERNAL COLOR CODES (Complete list)
    color_data = [
        ('RED', 'R'), ('ORANGE', 'O'), ('YELLOW', 'Y'), ('BLUE', 'B'),
        ('VIOLET', 'V'), ('GREEN', 'G'), ('BROWN', 'I'), ('GRAY', 'T'),
        ('BLACK', 'C'), ('GOLD', 'M'), ('SILVER', 'S'), ('MAGENTA', 'Z'),
        ('BEIGE', 'D'), ('PEACH', 'H'), ('PINK', 'K'), ('NATURAL', 'N')
    ]
    for c_name, c_code in color_data:
        InternalColor.objects.get_or_create(color=c_name, code=c_code)

    # 6. GIVE ADMIN ALL PERMISSIONS
    try:
        admin_role = Role.objects.get(department='Information Technology', role='ADMIN')
        all_access = AccessPoint.objects.all()
        for point in all_access:
            Permission.objects.get_or_create(role=admin_role, access=point, defaults={'is_enabled': True})
    except Role.DoesNotExist:
        pass

class Migration(migrations.Migration):
    dependencies = [
        ('main', '0001_initial'), # Points to the clean 0001 migration
    ]

    operations = [
        migrations.RunPython(populate_everything),
    ]