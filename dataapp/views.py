from django.shortcuts import render
from .srtrackingDataProcessingFunctions import get_sr_tracking_summary, enrich_sr_tracking_summary
from .srtrackingDataProcessingFunctions import get_monthly_tracking_percentages
from django.utils.timezone import now
from .plotly_funcs import fallidos_vs_completados_graph, failed_responsibility_breakdown_graph
from django.core.exceptions import ValidationError
from datetime import datetime
from usersapp.models import Company

def entregas_panel(req):
    return render(req, "kpisentregas.html")


def entregas_amba(req):
    
    return render(req, "entregas_amba.html")


def entregas_amba_gral(req):

    companies = Company.objects.all()

    df_query, cutoff_date = get_sr_tracking_summary(req)
    df_translated = enrich_sr_tracking_summary(df_query)
    relativized_df = get_monthly_tracking_percentages(df_translated)

    try:
        # Parse and validate start_date
        start_date = req.GET.get('start_date')
        if start_date:
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        else:
            start_date = cutoff_date  # Default to 12 months ago

        # Parse and validate end_date
        end_date = req.GET.get('end_date')
        if end_date:
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        else:
            end_date = now().date()  # Default to today

        # Swap dates if start_date is after end_date
        if start_date > end_date:
            start_date, end_date = end_date, start_date

    except (ValidationError, ValueError):
        # If invalid dates are passed, fallback to default range
        start_date = cutoff_date
        end_date = now().date()

    # Check for seller filtering (to be integrated later)
    sellers = req.GET.getlist('sellers')

    # Fetch and process data
    df_query, cutoff_date = get_sr_tracking_summary(req)
    df_translated = enrich_sr_tracking_summary(df_query)
    relativized_df = get_monthly_tracking_percentages(df_translated)

    # Generate graphs with the filtered data
    gral_graph_html = fallidos_vs_completados_graph(relativized_df, start_date, end_date, sellers)
    failed_graph_html = failed_responsibility_breakdown_graph(relativized_df, start_date, end_date, sellers)

    # Render the view with the context
    return render(req, "entregas_amba_gral.html", context={
        "gral_graph_html": gral_graph_html,
        "failed_graph_html": failed_graph_html,
        "companies": companies,
    })