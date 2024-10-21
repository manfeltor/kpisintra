from django.urls import path
from .views import base, unauthorized

urlpatterns = [
    path('', base, name="home"),
    path('unauthorized/', unauthorized, name="unauthorized"),
]
