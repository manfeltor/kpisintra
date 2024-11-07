from django.shortcuts import render

def entregas_panel(req):
    return render(req, "kpisentregas.html")


def entregas_amba(req):
    return render(req, "entregas_amba.html")