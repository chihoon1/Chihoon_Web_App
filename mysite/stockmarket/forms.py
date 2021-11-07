from django import forms
from .models import Stock


class StockNameForm(forms.ModelForm):
    class Meta:
        model = Stock
        fields = [
            'company'
        ]