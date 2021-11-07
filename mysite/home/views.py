from django.shortcuts import render
from django.views import View
from django.urls import reverse


# Create your views here.
class HomeClassView(View):
    template_name = "home.html"

    def get(self, request, *args, **kwargs):
        context = {
        }
        return render(request, self.template_name, context)

