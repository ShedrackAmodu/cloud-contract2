from django.urls import path
from .views import (
    DashboardView,
    ContractCreateView,
    ContractDetailView,
    ContractUpdateView,
    PublicContractsView,
    accept_contract,
    upload_contract_document,
    encryption_visualization_view
)

app_name = 'contracts'

urlpatterns = [
    path('', DashboardView.as_view(), name='dashboard'),
    path('create/', ContractCreateView.as_view(), name='create'),
    path('<int:pk>/', ContractDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', ContractUpdateView.as_view(), name='edit'),
    path('public/', PublicContractsView.as_view(), name='public'),
    path('<int:pk>/accept/', accept_contract, name='accept_contract'),
    path('<int:pk>/upload-document/', upload_contract_document, name='upload_document'),
    path('<int:pk>/encryption-visualization/', encryption_visualization_view, name='encryption_visualization'),
]
