from django import forms
from .models import Payment

class LoanForm(forms.Form):
    principal = forms.DecimalField(
        label="Principal Amount",
        min_value=0.01,
        max_digits=15,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter principal amount'})
    )
    interest_rate = forms.DecimalField(
        label="Interest Rate (%)",
        min_value=0,
        max_digits=5,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter interest rate'})
    )
    interest_mode = forms.ChoiceField(
        label="Interest Mode",
        choices=[('daily', 'Daily'), ('monthly', 'Monthly'), ('yearly', 'Yearly')],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    start_date = forms.DateField(
        label="Start Date",
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )

# loan_app/forms.py
class PaymentForm(forms.Form):
    date = forms.DateField(
        required=False,  # Add this
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    amount = forms.DecimalField(
        required=False,  # Add this
        min_value=0.01,
        max_digits=15,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Amount'})
    )