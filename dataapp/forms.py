from django import forms
from usersapp.models import Company

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