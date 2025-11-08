from django.urls import path
from . import views

app_name = 'oracle'
urlpatterns = [
    path('', views.list_pending_for_oracle, name='pending'),
    path('sign/<int:request_id>/', views.sign_request, name='sign'),
]
