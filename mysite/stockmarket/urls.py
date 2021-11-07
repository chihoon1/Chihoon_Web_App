from django.urls import path
from .views import MainView, GraphView, TickerView, StockView, PredictView

app_name = 'stockmarket'
urlpatterns = [
    path('', MainView.as_view(), name="main-page"),
    path('graph/', GraphView.as_view(), name="graph-page"),
    path('ticker/', TickerView.as_view(), name="ticker-page"),
    path('stock/', StockView.as_view(), name="stock-page"),
    path('predict/', PredictView.as_view(), name="predictor-page"),
]