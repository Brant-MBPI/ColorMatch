from django.db import migrations

def populate_all_data(apps, schema_editor):
    # Fetch all necessary models
    Role = apps.get_model('main', 'tbl_role')
    AccessPoint = apps.get_model('main', 'tbl_access_point')
    CodingMat = apps.get_model('main', 'tbl_coding_materials')
    Resin = apps.get_model('main', 'tbl_resins')
    InternalColor = apps.get_model('main', 'tbl_internal_color_code')

    # 1. Roles & Access Points (Previous requirement)
    roles = [('Information Technology', 'ADMIN'), ('Production', 'HEAD'), ('Production', 'STAFF')]
    for dept, role_name in roles:
        Role.objects.get_or_create(department=dept, role=role_name)
    
    access = ['Production Records', 'Dashboard', 'CMF', 'Feedback']
    for a in access:
        AccessPoint.objects.get_or_create(access_name=a)

    # 2. Coding Materials
    coding_data = [
        ('D', 'Pigment'), ('T', 'Metallic'), ('P', 'Pearlized'), ('M', 'Marble'), ('L', 'LINER')
    ]
    for c_code, c_name in coding_data:
        CodingMat.objects.get_or_create(code=c_code, name=c_name)

    # 3. Resins (Abbreviation - Code)
    resin_data = [
        ('PP', 'P'), ('PE', 'E'), ('PVC', 'V'), ('AS', 'S'), ('ABS', 'A'),
        ('GPPS', 'G'), ('HIPS', 'H'), ('UNIVERSAL', 'U'), ('PET', 'T'),
        ('EPS', 'X'), ('POLYCARBONATE', 'C'), ('EVA', 'EV'), ('NYLON', 'N')
    ]
    for abbr, r_code in resin_data:
        Resin.objects.get_or_create(abbreviation=abbr, code=r_code)

    # 4. Internal Color Codes (Color - Code)
    color_data = [
        ('RED', 'R'), ('ORANGE', 'O'), ('YELLOW', 'Y'), ('BLUE', 'B'),
        ('VIOLET', 'V'), ('GREEN', 'G'), ('BROWN', 'I'), ('GRAY', 'T'),
        ('BLACK', 'C'), ('GOLD', 'M'), ('SILVER', 'S'), ('MAGENTA', 'Z'),
        ('BEIGE', 'D'), ('PEACH', 'H'), ('PINK', 'K'), ('NATURAL', 'N')
    ]
    for c_name, c_code in color_data:
        InternalColor.objects.get_or_create(color=c_name, code=c_code)

class Migration(migrations.Migration):
    dependencies = [
        ('main', '0004_tbl_coding_materials_tbl_resins_and_more'), 
    ]

    operations = [
        migrations.RunPython(populate_all_data),
    ]