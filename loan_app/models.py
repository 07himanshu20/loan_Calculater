from django.db import models

class LoanCalculation(models.Model):
    principal = models.DecimalField(max_digits=15, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    INTEREST_MODES = [
        ('daily', 'Daily'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]
    interest_mode = models.CharField(max_length=10, choices=INTEREST_MODES, default='monthly')
    start_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

class Payment(models.Model):
    calculation = models.ForeignKey(LoanCalculation, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    date = models.DateField()