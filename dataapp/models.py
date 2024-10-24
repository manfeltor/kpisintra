from django.db import models
from usersapp.models import Company
import json

#TODO double check for fields config

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
    trackingDistribucion = models.CharField(max_length=100, blank=True, null=True)
    trackingTransporte = models.CharField(max_length=100, blank=True, null=True)
    codigoPostal = models.CharField(max_length=10)
    order_data = models.TextField(blank=True, null=True)  # Store as serialized dict string

    def __str__(self):
        return f"{self.seller.name} - {self.pedido} - {self.lpn}"
    
    # Method to convert customer_data back to dict
    @property
    def customer_data_as_dict(self):
        return json.loads(self.order_data) if self.order_data else {}
    

class PostalCodes(models.Model):
    cp = models.CharField(max_length=4, unique=True)
    localidad = models.CharField(max_length=100)
    partido = models.CharField(max_length=100)
    provincia = models.CharField(max_length=100)
    region = models.CharField(max_length=100)
    distrito = models.CharField(max_length=50)
    amba_intralog = models.BooleanField(default=False)
    flex = models.BooleanField(default=False)

    def __str__(self):
        return self.cp
