from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models

# Company Model
class Company(models.Model):
    name = models.CharField(max_length=100, unique=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    contact_email = models.EmailField(blank=True, null=True)
    contact_phone = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return self.name


# CustomUser model
class CustomUser(AbstractUser):
    MANAGER = 'manager'
    EMPLOYEE = 'employee'
    ADMIN = 'admin'
    CLIENT = 'client'

    ROLE_CHOICES = [
        (MANAGER, 'Manager'),
        (EMPLOYEE, 'Employee'),
        (ADMIN, 'Admin'),
        (CLIENT, 'Client'),
    ]

    phone_number = models.CharField(max_length=15, blank=True, null=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=EMPLOYEE)
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, related_name="users", null=True, blank=True)

    # Add related_name for groups and user_permissions to avoid clash with auth.User
    groups = models.ManyToManyField(Group, related_name="customuser_set", blank=True)
    user_permissions = models.ManyToManyField(Permission, related_name="customuser_permissions_set", blank=True)

    def __str__(self):
        return self.username

    @property
    def is_management(self):
        return self.role == self.MANAGER or self.role == self.ADMIN


# User Attribute Model
class UserAttribute(models.Model):
    EMPLOYEE = 'empleado'
    CLIENT = 'cliente'

    RELACION_CHOICES = [
        (EMPLOYEE, 'Empleado'),
        (CLIENT, 'Cliente'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='attributes')
    relacion = models.CharField(max_length=20, choices=RELACION_CHOICES, default=EMPLOYEE)
    # Use a ForeignKey to the Company model
    comp = models.ForeignKey(Company, on_delete=models.SET_NULL, related_name='user_attributes', null=True)

    def __str__(self):
        return f'{self.user.username} - {self.get_relacion_display()}'