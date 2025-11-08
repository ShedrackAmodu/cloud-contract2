from django.urls import path
from .views import retrieve

app_name = 'access_proxy'
urlpatterns = [
    path('retrieve/<int:data_request_id>/', retrieve, name='retrieve'),
]
