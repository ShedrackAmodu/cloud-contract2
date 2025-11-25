from django.urls import path
from . import views

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('public/', views.PublicContractsView.as_view(), name='public'),
    path('create/', views.ContractCreateView.as_view(), name='create'),
    path('<int:pk>/', views.ContractDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.ContractUpdateView.as_view(), name='edit'),
    path('<int:pk>/accept/', views.accept_contract, name='accept_contract'),
    path('<int:pk>/upload/', views.upload_contract_document, name='upload_document'),
    path('<int:pk>/visualization/', views.encryption_visualization_view, name='encryption_visualization'),
    path('<int:contract_pk>/document/<int:doc_pk>/', views.view_document, name='view_document'),
    path('<int:contract_pk>/view/<int:doc_pk>/', views.universal_viewer, name='universal_viewer'),
    path('<int:contract_pk>/download/<int:doc_pk>/', views.download_document, name='download_document'),
]