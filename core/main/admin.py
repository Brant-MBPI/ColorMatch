from django.contrib import admin

# Register your models here.
from .models import tbl_user, tbl_role

admin.site.register(tbl_user)
admin.site.register(tbl_role)
