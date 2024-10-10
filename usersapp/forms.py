from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from .models import CustomUser, Company
from dataapp.models import Order

class CompanyCreationForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['name', 'address', 'contact_email', 'contact_phone']
    
    def __init__(self, *args, **kwargs):
        super(CompanyCreationForm, self).__init__(*args, **kwargs)

       # Get distinct sellers from the Order model
        distinct_sellers = Order.objects.values_list('seller__name', flat=True).distinct()

        # Get companies already created
        existing_companies = Company.objects.values_list('name', flat=True)

        # Filter the dropdown to only show companies that haven't been created yet
        available_companies = [seller for seller in distinct_sellers if seller not in existing_companies]

        # Override the 'name' field as a ChoiceField for the dropdown
        self.fields['name'] = forms.ChoiceField(choices=[(company, company) for company in available_companies])

        # labels
        self.fields['name'].label = "Selecciona la compañia"
        self.fields['address'].label = "direccion"
        self.fields['contact_email'].label = "Email"
        self.fields['contact_phone'].label = "Telefono"
        
        # Add placeholders for form fields
        self.fields['name'].widget.attrs['placeholder'] = 'Nombre compañia'
        self.fields['address'].widget.attrs['placeholder'] = 'Direccion'
        self.fields['contact_email'].widget.attrs['placeholder'] = 'Mail'
        self.fields['contact_phone'].widget.attrs['placeholder'] = 'Telefono'
        
        # You can also customize validation error messages here if needed


class CustomUserCreationForm(UserCreationForm):
    company = forms.ModelChoiceField(queryset=Company.objects.all(), required=False)

    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'last_name', 'email', 'phone_number', 'role', 'company', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super(CustomUserCreationForm, self).__init__(*args, **kwargs)
        self.fields['role'].choices = [
            (CustomUser.EMPLOYEE, 'Employee'),
            (CustomUser.MANAGER, 'Manager'),
        ]

        # Customize labels and help texts
        self.fields['username'].label = "Nombre de usuario"
        self.fields['first_name'].label = "Nombre"
        self.fields['last_name'].label = "Apellido"
        self.fields['email'].label = "Email"
        self.fields['phone_number'].label = "Telefono"
        self.fields['role'].label = "Rol"
        self.fields['company'].label = "Compañía"
        self.fields['password1'].label = "Contraseña"
        self.fields['password2'].label = "Confirma contraseña"

        # Customize password validation error messages
        self.fields['password1'].error_messages = {
            'password_too_similar': "Contraseña muy similar a los datos.",
            'password_too_short': "La contraseña debe contener al menos 8 caracteres.",
            'password_too_common': "Contraseña muy común.",
            'password_entirely_numeric': "La contraseña no puede ser enteramente numérica.",
        }

        self.fields['password2'].error_messages = {
            'password_mismatch': "Las contraseñas no coinciden.",
        }

        self.fields['password1'].help_text = ""
        self.fields['password2'].help_text = ""
        self.fields['username'].help_text = "Máximo 150 caracteres entre letras, dígitos y @/./+/-/_ únicamente."

class UserProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'phone_number']

    def __init__(self, *args, **kwargs):
        super(UserProfileUpdateForm, self).__init__(*args, **kwargs)

        # Make profile fields optional
        self.fields['first_name'].required = False
        self.fields['last_name'].required = False
        self.fields['email'].required = False
        self.fields['phone_number'].required = False


        # self.fields['first_name'].widget.attrs['placeholder'] = 'Nombre'
        # self.fields['last_name'].widget.attrs['placeholder'] = 'Apellido'
        # self.fields['email'].widget.attrs['placeholder'] = 'email'
        # self.fields['phone_number'].widget.attrs['placeholder'] = 'Numero de telefono'

        self.fields['first_name'].label = 'Nombre'
        self.fields['last_name'].label = 'Apellido'
        self.fields['email'].label = 'email'
        self.fields['phone_number'].label = 'Numero de telefono'

class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super(CustomPasswordChangeForm, self).__init__(*args, **kwargs)

        self.fields['old_password'].widget.attrs['placeholder'] = 'Ingresa tu contraseña actual'
        self.fields['old_password'].label = 'Contraseña actual'
        self.fields['old_password'].help_text = 'Ingresa tu contraseña actual para verificar tu identidad.'

        self.fields['new_password1'].widget.attrs['placeholder'] = 'Ingresa tu nueva contraseña'
        self.fields['new_password1'].label = 'Nueva contraseña'
        self.fields['new_password1'].help_text = ''

        self.fields['new_password2'].widget.attrs['placeholder'] = 'Confirma tu nueva contraseña'
        self.fields['new_password2'].label = 'Nueva contraseña'
        self.fields['new_password2'].help_text = 'Reingresa tu nueva contraseña para confirmarla.'

        # Customize error messages
        self.fields['new_password1'].error_messages = {
            'password_too_similar': "Tu contraseña es muy similar a tu informacion personal.",
            'password_too_short': "Tu contraseña debe contener almenos 8 caracteres.",
            'password_too_common': "Tu contraseña es muy comun.",
            'password_entirely_numeric': "Tu contraseña no puede ser enteramente numerica.",
        }

        self.fields['new_password2'].error_messages = {
            'password_mismatch': "Los campos de nueva contraseña no coinciden.",
            'password_too_similar': "Tu contraseña es muy similar a tu informacion personal.",
            'password_too_short': "Tu contraseña debe contener almenos 8 caracteres.",
            'password_too_common': "Tu contraseña es muy comun.",
            'password_entirely_numeric': "Tu contraseña no puede ser enteramente numerica.",
        }

    def clean_old_password(self):
        old_password = self.cleaned_data.get('old_password')
        if not self.user.check_password(old_password):
            raise forms.ValidationError("La contraseña actual es incorrecta.")
        return old_password
    

class UserEditForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['role']
