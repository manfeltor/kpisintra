from django.urls import path
from .views import entregas_panel, entregas_amba, entregas_amba_gral

urlpatterns = [
    path('kpisentregas/', entregas_panel, name='kpisentregas'),
    path('kpisentregas/entregasamba', entregas_amba, name='entregas_amba'),
    path('kpisentregas/entregasambagral', entregas_amba_gral, name='entregas_amba_gral'),
]