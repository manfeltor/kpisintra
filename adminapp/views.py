from django.shortcuts import render

# Create your views here.
def adminpanel(req):
    return render(req, "admin_panel.html")
