from django import forms

from .models import ExtraPayment, Lease, MoneyTransaction, Payment, RentRate


class LeaseForm(forms.ModelForm):
    class Meta:
        model = Lease
        fields = ["title", "first_period_start", "currency"]
        widgets = {
            "first_period_start": forms.DateInput(attrs={"type": "date"}),
        }


class RentRateForm(forms.ModelForm):
    class Meta:
        model = RentRate
        fields = ["amount", "effective_date", "notes"]
        widgets = {
            "effective_date": forms.DateInput(attrs={"type": "date"}),
        }


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ["date", "amount", "status", "target_period_start", "notes"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "target_period_start": forms.DateInput(attrs={"type": "date"}),
        }


class ExtraPaymentForm(forms.ModelForm):
    class Meta:
        model = ExtraPayment
        fields = ["title", "description", "direction", "status", "agreed_date", "paid_date", "amount"]
        widgets = {
            "agreed_date": forms.DateInput(attrs={"type": "date"}),
            "paid_date": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 3}),
        }


class MoneyTransactionForm(forms.ModelForm):
    class Meta:
        model = MoneyTransaction
        fields = ["date", "amount", "notes", "payments_covered", "extra_payments_covered"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "payments_covered": forms.CheckboxSelectMultiple(),
            "extra_payments_covered": forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, lease=None, **kwargs):
        super().__init__(*args, **kwargs)
        if lease:
            self.fields["payments_covered"].queryset = Payment.objects.filter(lease=lease)
            self.fields["extra_payments_covered"].queryset = ExtraPayment.objects.filter(lease=lease)
