from django.db import models


class MacroEconomy(models.Model):
    # every attribute is a string form of json data type
    timestamp = models.TextField()
    fed_rate = models.TextField()
    longterm_treasury_yield = models.TextField()
    inflation_rate = models.TextField()
    unemployment_rate = models.TextField()  # 5
    gdp = models.TextField()  # 6
    vix = models.TextField()  # 7


class Stock(models.Model):
    # every attribute is a string form of json data type
    company = models.TextField()
    ticker = models.TextField()
    stock_price = models.TextField()
    dividends = models.TextField()
    volume = models.TextField()
    stock_splits = models.TextField()
    interval = models.TextField()
    financials = models.TextField()


class Predictor(models.Model):
    # every attribute is a string form of json data type
    type = models.TextField()
    timestamp = models.TextField()
    initial_probabilities = models.TextField()
    transition_probabilities = models.TextField()
    emission_probabilities = models.TextField()
    state_space = models.TextField()
    emission_space = models.TextField()