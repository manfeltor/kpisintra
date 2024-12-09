from django import forms
from usersapp.models import Company
from django.core.exceptions import ValidationError
from datetime import date

class FilterForm(forms.Form):
    start_date = forms.DateField(
        widget=forms.TextInput(attrs=
            {
                'type': 'date',
                'class': 'form-control custom-input'
            }
        ),
        label="Desde",
        required=False
    )
    end_date = forms.DateField(widget=forms.TextInput(attrs=
            {
                'type': 'date',
                'class': 'form-control custom-input'
            }
        ),
        label="Hasta",
        required=False
    )
    sellers = forms.ModelMultipleChoiceField(
        queryset=Company.objects.all(),
        widget=forms.CheckboxSelectMultiple(
            # queryset=Company.objects.all(),
            attrs=
            {
                'class': 'form-control custom-select'
            }
        ),
        label="Sellers",
        required=False
    )

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        # Validate start_date and end_date
        if start_date and end_date:
            if start_date > end_date:
                raise ValidationError("La fecha 'desde' no puede ser anterior a 'hasta'.")

        # Ensure dates are not in the future
        today = date.today()
        if start_date and start_date > today:
            raise ValidationError("La fecha de inicio no puede ser en el futuro.")
        if end_date and end_date > today:
            raise ValidationError("La fecha final no puede ser en el futuro.")
        
        return cleaned_data