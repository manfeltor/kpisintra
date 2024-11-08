from django.urls import path
from .views import entregas_panel, entregas_amba

urlpatterns = [
    path('kpisentregas/', entregas_panel, name='kpisentregas'),
    path('kpisentregas/entregasamba', entregas_amba, name='entregas_amba'),
]