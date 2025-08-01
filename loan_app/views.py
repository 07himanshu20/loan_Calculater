# loan_app/views.py
from django.shortcuts import render, redirect
from django.views import View
from datetime import date, datetime
from decimal import Decimal
from .forms import LoanForm
from django.contrib import messages
from django.template.defaulttags import register

@register.filter
def div(value, arg):
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return 0

class CalculatorView(View):
    template_name = 'loan_app/calculator.html'
    
    def get(self, request):
        # Clear session data on new page load
        request.session.pop('payments', None)
        request.session.pop('loan_data', None)
        
        loan_form = LoanForm()
        return render(request, self.template_name, {
            'loan_form': loan_form,
            'payments': []
        })
    
    def post(self, request):
        # Initialize form with session data if available
        loan_data = request.session.get('loan_data', {})
        loan_form = LoanForm(loan_data or request.POST)
        payments = request.session.get('payments', [])
        
        # Handle adding payments
        if 'add_payment' in request.POST:
            date_val = request.POST.get('date')
            amount_val = request.POST.get('amount')
            
            if date_val and amount_val:
                try:
                    # Validate and convert to proper types
                    datetime.strptime(date_val, '%Y-%m-%d')  # Validate date format
                    float(amount_val)  # Validate numeric amount
                    
                    payments.append({
                        'date': date_val,
                        'amount': amount_val
                    })
                    request.session['payments'] = payments
                    messages.success(request, "Payment added successfully!")
                    
                    # Save loan data to session
                    if loan_form.is_valid():
                        # Convert to float for session storage
                        loan_data = {
                            'principal': float(loan_form.cleaned_data['principal']),
                            'interest_rate': float(loan_form.cleaned_data['interest_rate']),
                            'interest_mode': loan_form.cleaned_data['interest_mode'],
                            'start_date': loan_form.cleaned_data['start_date'].isoformat(),
                        }
                        request.session['loan_data'] = loan_data
                except ValueError:
                    messages.error(request, "Invalid payment data")
            else:
                messages.error(request, "Please fill both date and amount fields")
        
        # Handle removing payments
        elif 'remove_payment' in request.POST:
            index = int(request.POST.get('remove_payment'))
            if 0 <= index < len(payments):
                del payments[index]
                request.session['payments'] = payments
                messages.info(request, "Payment removed successfully!")
                
                # Save loan data to session
                if loan_form.is_valid():
                    loan_data = {
                        'principal': float(loan_form.cleaned_data['principal']),
                        'interest_rate': float(loan_form.cleaned_data['interest_rate']),
                        'interest_mode': loan_form.cleaned_data['interest_mode'],
                        'start_date': loan_form.cleaned_data['start_date'].isoformat(),
                    }
                    request.session['loan_data'] = loan_data
        
        # Handle calculation
        elif 'calculate' in request.POST:
            if loan_form.is_valid():
                # Clear session data after calculation
                request.session.pop('payments', None)
                request.session.pop('loan_data', None)
                return self.calculate_loan(request, loan_form.cleaned_data, payments)
            else:
                messages.error(request, "Please fill all loan details correctly")
        
        # Handle reset
        elif 'reset' in request.POST:
            request.session.pop('payments', None)
            request.session.pop('loan_data', None)
            return redirect('calculator')
        
        # Handle form initialization from session
        if loan_data:
            # Convert session data back to form-compatible format
            loan_form = LoanForm(initial={
                'principal': loan_data['principal'],
                'interest_rate': loan_data['interest_rate'],
                'interest_mode': loan_data['interest_mode'],
                'start_date': loan_data['start_date'],
            })
        
        return render(request, self.template_name, {
            'loan_form': loan_form,
            'payments': payments
        })
    
    def calculate_interest(self, principal, rate, days, mode):
        principal = Decimal(str(principal))
        rate = Decimal(str(rate))
        days = Decimal(str(days))
        
        if principal <= Decimal('0'):
            return Decimal('0')
            
        if mode == 'daily':
            return principal * (rate / Decimal('100')) * days
        elif mode == 'monthly':
            return principal * (rate / Decimal('100')) * (days / Decimal('30'))
        elif mode == 'yearly':
            return principal * (rate / Decimal('100')) * (days / Decimal('365'))
    
    def calculate_loan(self, request, loan_data, payment_data):
        # Convert to Decimal for calculations
        principal = Decimal(str(loan_data['principal']))
        rate = Decimal(str(loan_data['interest_rate']))
        mode = loan_data['interest_mode']
        start_date = loan_data['start_date']
        
        # Convert payments to proper format
        payments = []
        for p in payment_data:
            try:
                payment_date = datetime.strptime(p['date'], '%Y-%m-%d').date()
                amount = Decimal(p['amount'])
                payments.append((payment_date, amount))
            except:
                continue
        
        # Sort payments by date
        payments.sort(key=lambda x: x[0])
        
        # Initialize tracking variables
        current_balance = principal
        last_date = start_date
        total_interest = Decimal('0')
        total_paid = Decimal('0')
        overpayment = Decimal('0')
        payment_history = []
        
        # Process each payment
        for payment_date, amount in payments:
            # Calculate days since last transaction
            days = (payment_date - last_date).days
            if days < 0:
                continue  # Skip invalid dates

            # Calculate interest for the period
            interest = self.calculate_interest(current_balance, rate, days, mode)
            total_interest += interest
            
            # Update balance with interest
            current_balance += interest
            
            # Process payment
            if amount > current_balance:
                # Handle overpayment
                overpayment += amount - current_balance
                payment_history.append({
                    'date': payment_date,
                    'days': days,
                    'interest': float(interest),
                    'payment': float(amount),
                    'principal_paid': float(current_balance),
                    'overpayment': float(amount - current_balance),
                    'new_balance': 0
                })
                total_paid += current_balance
                current_balance = Decimal('0')
            else:
                # Normal payment
                current_balance -= amount
                total_paid += amount
                payment_history.append({
                    'date': payment_date,
                    'days': days,
                    'interest': float(interest),
                    'payment': float(amount),
                    'principal_paid': float(amount),
                    'overpayment': 0,
                    'new_balance': float(current_balance)
                })
                
            last_date = payment_date

        # Calculate interest from last payment to today
        today = date.today()
        final_days = (today - last_date).days
        if final_days < 0:
            final_days = 0
            
        final_interest = self.calculate_interest(current_balance, rate, final_days, mode)
        total_interest += final_interest
        current_balance += final_interest
        
        # Prepare context for results
        context = {
            'principal': float(principal),
            'rate': float(rate),
            'mode': mode,
            'start_date': start_date,
            'total_paid': float(total_paid),
            'total_interest': float(total_interest),
            'overpayment': float(overpayment),
            'final_interest': float(final_interest),
            'current_balance': float(current_balance),
            'final_days': final_days,
            'payment_history': payment_history,
            'today': today,
        }
        
        return render(request, 'loan_app/results.html', context)