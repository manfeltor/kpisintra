from django.db import models
from usersapp.models import Company

#TODO rearmar este modelo con los datos naturales del OMS

class Order(models.Model):
    seller = models.ForeignKey(Company, on_delete=models.SET_NULL, related_name="orders")
    pedido = models.CharField(max_length=100)
    lpn = models.CharField(max_length=100, unique=True)
    trackingca = models.CharField(max_length=100, unique=True)
    trackingsr = models.CharField(max_length=100, unique=True)
    order_date = models.DateField()
    customer_data = models.TextField(blank=True, null=True)  # Store as serialized dict string

    def __str__(self):
        return f"{self.seller.name} - {self.pedido} - {self.lpn}"
    
    # Method to convert customer_data back to dict
    @property
    def customer_data_as_dict(self):
        return json.loads(self.customer_data) if self.customer_data else {}