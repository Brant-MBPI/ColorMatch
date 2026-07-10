from django.db import migrations

def sync_roles_and_access(apps, schema_editor):
    Role = apps.get_model('main', 'tbl_role')
    AccessPoint = apps.get_model('main', 'tbl_access_point')
    Permission = apps.get_model('main', 'tbl_role_permissions')

    # 1. THE COMPLETE ROLES LIST
    roles_list = [
        ('Information Technology', 'ADMIN'),
        ('Production', 'HEAD'),
        ('Production', 'STAFF'),
        ('Laboratory', 'HEAD'),
        ('Laboratory', 'STAFF'),
        ('sales', 'SALES')
    ]
    for dept, role_name in roles_list:
        Role.objects.get_or_create(department=dept, role=role_name)

    # 2. THE COMPLETE ACCESS LIST
    access_list = [
        'Dashboard', 'CMF Records', 'CMF Entry', 'RS Entry', 
        'MB Formula', 'DC Formula', 'Pending Completed', 
        'Feedback', 'Audit Trail', 'Permission Access'
    ]
    for name in access_list:
        AccessPoint.objects.get_or_create(access_name=name)

    # 3. ENSURE ADMIN HAS EVERYTHING ENABLED
    try:
        admin_role = Role.objects.get(department='Information Technology', role='ADMIN')
        all_access = AccessPoint.objects.all()
        for point in all_access:
            # This will create permissions for any new points added above
            Permission.objects.get_or_create(role=admin_role, access=point, defaults={'is_enabled': True})
            # This ensures even existing ones are set to True for Admin
            Permission.objects.filter(role=admin_role, access=point).update(is_enabled=True)
    except Role.DoesNotExist:
        pass

class Migration(migrations.Migration):
    dependencies = [
        ('main', '0005_auto_20260710_1100'),
    ]

    operations = [
        migrations.RunPython(sync_roles_and_access),
    ]