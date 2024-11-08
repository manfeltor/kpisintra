from django.shortcuts import render
from .main_functions import get_orders_dataframe

def entregas_panel(req):
    return render(req, "kpisentregas.html")


def entregas_amba(req):
    df = get_orders_dataframe(fields=['pedido'], SRdeserialization=['title'])
    html_table = df.head(20).to_html(classes="table table-striped table-bordered", index=False)
    
    return render(req, "entregas_amba.html", {"table": html_table})