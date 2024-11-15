from django.shortcuts import render
from .main_functions import get_orders_dataframe

def entregas_panel(req):
    return render(req, "kpisentregas.html")


def entregas_amba(req):
    
    return render(req, "entregas_amba.html")

def entregas_amba_gral(req):
    
    return render(req, "entregas_amba_gral.html")