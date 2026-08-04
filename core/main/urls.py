from django.urls import path

from . import views
from .services.cmf_records import cmf_records_services, previous_cmf_record
from .services.export import cmf_record_export

urlpatterns = [
    path('', views.index, name='index'),
    path('pending-role/', views.pending_role, name='pending_role'),
    path('login/signin/', views.signin, name='signin'),
    path('login/signup/', views.signup, name='signup'),
    path('login/signout/', views.signout, name='signout'),
    path('other/', views.otherPage, name='other'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('cmf/records/', views.cmf_records, name='cmf_records'),
    path('cmf/entry/', views.cmf_entry, name='cmf_entry'),
    path('cmf/rs-entry/', views.cmf_rs_entry, name='rs_entry'),
    path('cmf/mb-formula/', views.cmf_mb_formula, name='mb_formula'),
    path('cmf/dc-formula/', views.cmf_dc_formula, name='dc_formula'),
    path('cmf/pending-completed/', views.cmf_pending_completed, name='pending_completed'),
    path('master-formula/', views.master_formula, name='master_formula'),
    path('feedback/', views.feedback, name='feedback'),
    path('audit-trail/', views.audit_trail, name='audit_trail'),
    path('legacy/sync/', views.trigger_legacy_sync, name='trigger_legacy_sync'),

    # export
    path('cmf/records/export/', views.cmf_records_export_preview, name='cmf_records_export_preview'),
    # with parameters
    path('cmf/records/<str:cm_no>/', views.cmf_record_detail, name='cmf_record_detail'),
    path('cmf/formula/<str:formula_type>/<int:formula_id>/toggle-final/', cmf_records_services.toggle_final_formula, name='toggle_final_formula'),
    path('cmf/rs-records/<int:rs_id>/', views.rs_record_detail, name='rs_record_detail'),
    # ajax
    path('check-previous-matching/', previous_cmf_record.check_previous_matching, name='check_previous_matching'),
    path('master-formula/<int:form_id>/materials/', views.master_formula_materials_json, name='master_formula_materials_json'),
]