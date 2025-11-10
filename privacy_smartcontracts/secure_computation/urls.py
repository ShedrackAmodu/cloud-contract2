from django.urls import path
from . import views

app_name = 'secure_computation'

urlpatterns = [
    path('tee-dashboard/', views.tee_dashboard, name='tee_dashboard'),
    path('validation/<int:validation_id>/', views.tee_validation_detail, name='validation_detail'),
]
