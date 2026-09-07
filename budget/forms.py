from decimal import Decimal
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Budget, MONEY_FIELDS, CATEGORIES


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(label='E-Mail-Adresse', help_text='Damit du dein Passwort zurücksetzen kannst.')

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ['username', 'email']


class BudgetForm(forms.ModelForm):
    month = forms.DateField(input_formats=['%Y-%m'], widget=forms.DateInput(format='%Y-%m', attrs={'type': 'month'}))

    class Meta:
        model = Budget
        fields = ['month', *MONEY_FIELDS, 'cut']
        labels = {'income': 'Monatliches Nettoeinkommen', 'cut': 'Wunsch-Reduktion', **dict(CATEGORIES)}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for key in MONEY_FIELDS:
            self.fields[key].required = False
            self.fields[key].widget.attrs.update({
                'id': key, 'inputmode': 'decimal', 'min': '0', 'max': '1000000',
                'step': '0.01', 'placeholder': '0,00', 'autocomplete': 'off',
            })
        self.fields['cut'].widget = forms.NumberInput(attrs={'id': 'cut', 'type': 'range', 'min': 0, 'max': 50})

    def clean(self):
        cleaned = super().clean()
        for key in MONEY_FIELDS:
            if key not in self.errors and cleaned.get(key) is None:
                cleaned[key] = Decimal('0')
        return cleaned

    def clean_month(self):
        value = self.cleaned_data['month']
        if not 2000 <= value.year <= 2100:
            raise forms.ValidationError('Bitte wähle einen Monat zwischen 2000 und 2100.')
        return value.replace(day=1)
