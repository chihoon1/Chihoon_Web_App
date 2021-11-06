"""mysite URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.urls import include
from home.views import HomeClassView
#from stockmarket.views import StockView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('stockmarket/', include('stockmarket.urls', namespace='stockmarket')),
    path('gomoku/', include('gomoku.urls', namespace='gomoku')),
    #path('stockmarket/', StockView.as_view(), name="stockmarket-page"),
    #path('', home_view, name="home-view"),
    #path('about/', about_view, name="about-view"),
    path('', HomeClassView.as_view(), name="home-view"),
    path('about/', HomeClassView.as_view(template_name="about.html"), name="about-view"),
    path('contact/', HomeClassView.as_view(template_name="contact.html"), name="contact-view"),
]


'''
from django.contrib import admin
from django.urls import path

urlpatterns = [
    path('admin/', admin.site.urls),
]
'''
