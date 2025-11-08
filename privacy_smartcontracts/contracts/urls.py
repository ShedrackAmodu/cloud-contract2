from django.urls import path
from .views import DashboardView, ContractCreateView, ContractDetailView, ContractUpdateView

app_name = 'contracts'

urlpatterns = [
    path('', DashboardView.as_view(), name='dashboard'),
    path('create/', ContractCreateView.as_view(), name='create'),
    path('<int:pk>/', ContractDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', ContractUpdateView.as_view(), name='edit'),
]
