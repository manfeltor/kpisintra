from django.urls import path
from .views import adminpanel

urlpatterns = [
    path('', adminpanel, name="adminpanel"),
]