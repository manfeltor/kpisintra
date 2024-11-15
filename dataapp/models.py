from django.db import models
from usersapp.models import Company
import json
from django.core.validators import MaxValueValidator

SR_rawJson_keys = [
    "id", "load", "tags", "fleet", "notes", "order", "route", "title", "driver",
    "load_2", "load_3", "seller", "status", "address", "created", "vehicle",
    "duration", "latitude", "modified", "pictures", "priority", "has_alert",
    "longitude", "reference", "signature", "on_its_way", "visit_type",
    "window_end", "current_eta", "eta_current", "tracking_id", "checkin_time",
    "contact_name", "planned_date", "window_end_2", "window_start",
    "checkout_time", "contact_email", "contact_phone", "eta_predicted",
    "geocode_alert", "priority_level", "window_start_2", "programmed_date",
    "skills_optional", "skills_required", "checkout_comment", "checkout_latitude",
    "checkout_longitude", "extra_field_values", "checkout_observation",
    "estimated_time_arrival", "estimated_time_departure", "route_estimated_time_start"
]

sr_checkout_observations_matrix = {
    "1068d8b8-f939-46f7-8819-6ab130329ce9": {
        "type": "failed",
        "label": "fueraDeRutaAsignada",
        "responsibility": "transporte"
    },
    "b068cd31-74c3-4f36-b60a-5f0a7b8837dd": {
        "type": "completed",
        "label": "Entregado",
        "responsibility": None
    },
    "e1b34560-430b-450d-a4df-55066d09172d": {
        "type": "completed",
        "label": "colectado",
        "responsibility": None
    },
    "90fce0c5-4271-40f3-9f4f-71a6e3ee6e23": {
        "type": "failed",
        "label": "ausente",
        "responsibility": "cliente"
    },
    "c689bc80-a295-458e-a858-1251afc1925c": {
        "type": "completed",
        "label": "devolucionCliente",
        "responsibility": None
    },
    "1190098c-5ae2-467f-9ff8-ab839ac0555a": {
        "type": "failed",
        "label": "domicilioIncorrecto",
        "responsibility": "cliente"
    },
    "4ae3ce34-2dc2-4a23-935b-93a7b0001875": {
        "type": "failed",
        "label": "cancelado",
        "responsibility": "cliente"
    },
    "9e4619d2-240f-4efb-bc73-f91e9469cd91": {
        "type": "failed",
        "label": "mercaderiaNoDespachada",
        "responsibility": "transporte"
    },
    "d608375c-23cd-4ea3-bce8-25bfacc74ede": {
        "type": "failed",
        "label": "zonaPeligrosa",
        "responsibility": "cliente"
    },
    "b77cf748-cd66-4c33-bdac-4b2ab0534b2b": {
        "type": "failed",
        "label": "rechazado",
        "responsibility": "cliente"
    },
    "1a10310b-e710-4d66-8153-44ca9a88a8dc": {
        "type": "failed",
        "label": "noColectado",
        "responsibility": "transporte"
    },
    "853eaa3c-c265-4c4d-96ef-95fe580114fe": {
        "type": "failed",
        "label": "demorasOperativas",
        "responsibility": "transporte"
    }
}


class SRTrackingData(models.Model):
    tracking_id = models.CharField(max_length=100, unique=True)
    rawJson = models.JSONField(null=True, blank=True)
    status = models.CharField(max_length=25)
    title = models.CharField(max_length=200)
    tipo = models.CharField(max_length=25, blank=True, null=True)
    pedido = models.CharField(max_length=25, blank=True, null=True)
    seller = models.CharField(max_length=25, blank=True, null=True)
    reference = models.CharField(max_length=50)
    checkout_observation= models.CharField(max_length=50)
    planned_date = models.DateField()
    

class CATrackingData(models.Model):
    trackingTransporte = models.CharField(max_length=100, unique=True)
    rawJson = models.JSONField(null=True, blank=True)
    

class PostalCodes(models.Model):
    cp = models.CharField(max_length=4, unique=True)
    localidad = models.CharField(max_length=100)
    partido = models.CharField(max_length=100)
    provincia = models.CharField(max_length=100)
    region = models.CharField(max_length=100)
    distrito = models.CharField(max_length=50)
    amba_intralog = models.BooleanField(default=False)
    flex = models.BooleanField(default=False)
    dias_limite = models.PositiveIntegerField(validators=[MaxValueValidator(99)])

    def __str__(self):
        return self.cp


class Order(models.Model):
    pedido = models.CharField(max_length=100)
    flujo = models.CharField(max_length=10)
    seller = models.ForeignKey(Company, on_delete=models.SET_NULL, related_name="orders", null=True)
    sucursal = models.CharField(max_length=50)
    estadoPedido = models.CharField(max_length=50)
    fechaCreacion = models.DateTimeField()
    fechaRecepcion = models.DateTimeField(blank=True, null=True)
    tipo = models.CharField(max_length=50)
    fechaDespacho = models.DateTimeField(blank=True, null=True)
    fechaEntrega = models.DateTimeField(blank=True, null=True)
    lpn = models.CharField(max_length=100, unique=True)
    estadoLpn = models.CharField(max_length=100)
    provincia = models.CharField(max_length=100)
    localidad = models.CharField(max_length=100)
    zona = models.CharField(max_length=100)
    trackingDistribucion = models.CharField(max_length=100, blank=True, null=True)
    # trackingDistribucion = models.ForeignKey(SRTrackingData, on_delete=models.CASCADE, related_name="tracking_distribucion", null=True, blank=True)
    trackingTransporte = models.ForeignKey(CATrackingData, on_delete=models.CASCADE, related_name="tracking_transporte", null=True, blank=True)
    # trackingTransporte = models.CharField(max_length=100, blank=True, null=True)
    codigoPostaltxt = models.CharField(max_length=10)
    codigoPostal = models.ForeignKey(PostalCodes, on_delete=models.SET_NULL, related_name="postal_codes", null=True)
    order_data = models.TextField(blank=True, null=True)  # Store as serialized dict string

    def __str__(self):
        return f"{self.seller.name} - {self.pedido} - {self.lpn}"
    
    # Method to convert customer_data back to dict
    @property
    def customer_data_as_dict(self):
        return json.loads(self.order_data) if self.order_data else {}