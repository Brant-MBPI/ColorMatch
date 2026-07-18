from django.urls import path
from . import views
from .services.cmf_records import cmf_records_services

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
    path('feedback', views.feedback, name='feedback'),
    path('audit-trail/', views.audit_trail, name='audit_trail'),


    path('cmf/records/<str:cm_no>/', cmf_records_services.get_cmf_formulas, name='get_formulas'),
]