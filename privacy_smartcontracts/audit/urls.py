from django.urls import path
from . import views

urlpatterns = [
    path('list/', views.audit_list, name='audit_list'),
    path('export/', views.export_csv, name='export_audit'),
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
]
