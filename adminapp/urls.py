from django.urls import path
from .views import adminpanel, process_orders_from_upload, db_manager, download_template_xlsx, delete_all_orders
from .views import upload_postal_codes, download_cp_template_xlsx

urlpatterns = [
    path('', adminpanel, name="adminpanel"),
    path('dbmanager/', db_manager, name="db_manager"),
    path('uploadomsdata/', process_orders_from_upload, name='upload_oms_data'),
    path('delete-all-orders/', delete_all_orders, name='delete_all_orders'),
    path('download-template/', download_template_xlsx, name='download_template_xlsx'),
    path('uploadpostal/', upload_postal_codes, name='upload_postal_codes'),
    path('download-cptemplate/', download_cp_template_xlsx, name='download_cp_template_xlsx'),
]