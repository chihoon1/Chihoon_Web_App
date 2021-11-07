from django.contrib import admin
from .models import  MacroEconomy, Stock, Predictor

# Register your models here.
admin.site.register(MacroEconomy)
admin.site.register(Stock)
admin.site.register(Predictor)