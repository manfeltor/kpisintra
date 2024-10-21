from django.urls import path
from .views import adminpanel, process_orders_from_upload, db_manager, download_template_xlsx

urlpatterns = [
    path('', adminpanel, name="adminpanel"),
    path('dbmanager/', db_manager, name="db_manager"),
    path('uploadomsdata/', process_orders_from_upload, name='upload_oms_data'),
    path('download-template/', download_template_xlsx, name='download_template_xlsx'),
]