from django.shortcuts import render

# Create your views here.

def base(req):
    return render(req, "landing.html")

def unauthorized(req):
    return render(req, "unauthorized.html")