from django.shortcuts import render
from .srtrackingDataProcessingFunctions import get_sr_tracking_summary, enrich_sr_tracking_summary
from .srtrackingDataProcessingFunctions import get_monthly_tracking_percentages
from django.utils.timezone import now
from .plotly_funcs import fallidos_vs_completados_graph, failed_responsibility_breakdown_graph

def entregas_panel(req):
    return render(req, "kpisentregas.html")


def entregas_amba(req):
    
    return render(req, "entregas_amba.html")

def entregas_amba_gral(req):

    df_query, cutoff_date = get_sr_tracking_summary(req)
    df_translated = enrich_sr_tracking_summary(df_query)
    relativized_df = get_monthly_tracking_percentages(df_translated)

    if req.GET.get('start_date'):
        start_date = req.GET.get('start_date')
    else:
        start_date = cutoff_date
    if req.GET.get('end_date'):
        end_date = req.GET.get('end_date')
    else:
        end_date =now()
    if req.GET.get('seller'):
        seller = req.GET.get('seller')
    else:
        seller = None

    gral_graph_html = fallidos_vs_completados_graph(relativized_df, start_date, end_date, seller)
    failed_graph_html = failed_responsibility_breakdown_graph(relativized_df, start_date, end_date, seller)

    
    return render(req, "entregas_amba_gral.html", context={
         "gral_graph_html": gral_graph_html, "failed_graph_html" : failed_graph_html
        })