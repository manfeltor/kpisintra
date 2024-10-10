from django.urls import path
from .views import adminpanel, process_orders_from_upload

urlpatterns = [
    path('', adminpanel, name="adminpanel"),
    path('uploadomsdata/', process_orders_from_upload, name='upload_oms_data'),
]