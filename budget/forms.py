from django import forms
from .models import Budget, MONEY_FIELDS

class BudgetForm(forms.ModelForm):
    month = forms.DateField(input_formats=['%Y-%m'], widget=forms.DateInput(format='%Y-%m', attrs={'type': 'month'}))

    class Meta:
        model = Budget
        fields = ['month', *MONEY_FIELDS, 'cut']

    def clean_month(self):
        return self.cleaned_data['month'].replace(day=1)
