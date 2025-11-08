from django.urls import path
from . import views

app_name = 'requests_app'
urlpatterns = [
    path('create/<int:contract_id>/', views.create_request, name='create_request'),
    path('mine/', views.my_requests, name='my_requests'),
    path('owner/', views.contract_requests_for_owner, name='owner_requests'),
    path('process/<int:request_id>/<str:action>/', views.process_request, name='process_request'),
]
