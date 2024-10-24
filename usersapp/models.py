from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models

# Company Model
class Company(models.Model):
    name = models.CharField(max_length=100, unique=True)
    omni = models.BooleanField(default=False)
    interior = models.BooleanField(default=False)
    wh = models.BooleanField(default=False)

    def __str__(self):
        return self.name


# CustomUser model
class CustomUser(AbstractUser):
    MANAGER = 'manager'
    EMPLOYEE = 'employee'
    CLIENT = 'client'

    ROLE_CHOICES = [
        (MANAGER, 'Manager'),
        (EMPLOYEE, 'Empleado'),
        (CLIENT, 'Cliente'),
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
        return self.role == self.MANAGER