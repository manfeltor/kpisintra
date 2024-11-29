from django.urls import path
from .views import entregas_panel, entregas_amba, entregas_amba_gral, entregas_amba_failed, entregas_interior
from .views import entregas_interior_central_stats, entregas_interior_descriptive_stats, entregas_amba_descr

urlpatterns = [
    path('kpisentregas/', entregas_panel, name='kpisentregas'),
    path('kpisentregas/entregasamba', entregas_amba, name='entregas_amba'),
    path('kpisentregas/entregasambagral', entregas_amba_gral, name='entregas_amba_gral'),
    path('kpisentregas/entregasambafailed', entregas_amba_failed, name='entregas_amba_failed'),
    path('kpisentregas/zone', entregas_amba_descr, name='entregas_amba_descr'),
    path('kpisentregas/entregasinterior', entregas_interior, name='entregas_interior'),
    path('kpisentregas/entregasinterior/centraltendency', entregas_interior_central_stats, name='entregas_interior_central'),
    path('kpisentregas/entregasinterior/descriptive', entregas_interior_descriptive_stats, name='entregas_interior_descriptive'),
    ]