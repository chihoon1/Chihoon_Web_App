from django.shortcuts import render
from django.views import View
from django.urls import reverse


# Create your views here.
class HomeClassView(View):
    template_name = "home.html"
    #style_location = "static/" # reverse("home-view")

    def get(self, request, *args, **kwargs):
        context = {
        }
        return render(request, self.template_name, context)


''' def home_view(request, *args, **kwargs):
    template_style = "" # "static/"
    context = {
        "style_path": template_style
    }
    return render(request, "home.html", context)
    #return render(request, "navbar.html", context)

def about_view(request, *args, **kwargs):
    style_location = ""
    context = {
        "style_path": style_location
    }
    return render(request, "about.html", context)
'''
