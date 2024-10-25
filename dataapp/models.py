from django.db import models
from usersapp.models import Company
import json
from django.core.validators import MaxValueValidator

#TODO double check for fields config


class SRTrackingData(models.Model):
    trackingDistribucion = models.CharField(max_length=100, unique=True)
    otherData1 = models.CharField(max_length=100)
    otherData2 = models.CharField(max_length=100)
    otherData3 = models.CharField(max_length=100)


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
    fechaDespacho = models.DateTimeField(blank=True, null=True)
    fechaEntrega = models.DateTimeField(blank=True, null=True)
    lpn = models.CharField(max_length=100, unique=True)
    estadoLpn = models.CharField(max_length=100)
    provincia = models.CharField(max_length=100)
    localidad = models.CharField(max_length=100)
    zona = models.CharField(max_length=100)
    # trackingDistribucion = models.CharField(max_length=100, blank=True, null=True)
    trackingDistribucion = models.ForeignKey(SRTrackingData, on_delete=models.CASCADE, related_name="tracking_distribucion", null=True, blank=True)
    trackingTransporte = models.CharField(max_length=100, blank=True, null=True)
    codigoPostaltxt = models.CharField(max_length=10)
    codigoPostal = models.ForeignKey(PostalCodes, on_delete=models.SET_NULL, related_name="postal_codes", null=True)
    order_data = models.TextField(blank=True, null=True)  # Store as serialized dict string

    def __str__(self):
        return f"{self.seller.name} - {self.pedido} - {self.lpn}"
    
    # Method to convert customer_data back to dict
    @property
    def customer_data_as_dict(self):
        return json.loads(self.order_data) if self.order_data else {}
    

