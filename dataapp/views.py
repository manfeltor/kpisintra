from django.shortcuts import render
from .srtrackingDataProcessingFunctions import get_sr_tracking_summary, enrich_sr_tracking_summary
from .srtrackingDataProcessingFunctions import get_monthly_tracking_percentages
from django.utils.timezone import now
from .plotly_funcs import fallidos_vs_completados_graph, failed_responsibility_breakdown_graph
from .plotly_funcs import failed_responsibility_desambiguation_transport_vs_client, create_bar_chart
# from django.core.exceptions import ValidationError
# from datetime import datetime, timedelta
from usersapp.models import Company, CustomUser
from .forms import FilterForm
from .main_functions import define_dates_and_sellers
from .orderDataProcessingFunctions import query_primary_order_df_interior, enrich_primary_df_timedeltas


def entregas_panel(req):
    return render(req, "kpisentregas.html")


def entregas_amba(req):
    
    return render(req, "entregas_amba.html")


def entregas_amba_gral(req):

    companies = Company.objects.all()

    form = FilterForm(req.POST or None)

    start_date, end_date, sellers = define_dates_and_sellers(req, form)

    df_query = get_sr_tracking_summary(req, sellers)
    df_translated = enrich_sr_tracking_summary(df_query)
    relativized_df = get_monthly_tracking_percentages(df_translated, "responsibility")    

    gral_graph_html = fallidos_vs_completados_graph(relativized_df, start_date, end_date, sellers)
    failed_graph_html = failed_responsibility_breakdown_graph(relativized_df, start_date, end_date, sellers)

    if req.user.role == CustomUser.CLIENT:
        usr_role = None
    else:
        usr_role = 1

    return render(req, "entregas_amba_gral.html", context={
        "gral_graph_html": gral_graph_html,
        "failed_graph_html": failed_graph_html,
        "companies": companies,
        "form": form,
        "usr_role": usr_role
    })


def entregas_amba_failed(req):

    companies = Company.objects.all()

    form = FilterForm(req.POST or None)

    start_date, end_date, sellers = define_dates_and_sellers(req, form)

    df_query = get_sr_tracking_summary(req, sellers, failed=False)
    df_translated = enrich_sr_tracking_summary(df_query)
    relativized_df = get_monthly_tracking_percentages(df_translated, 'label')

    # # Ensure start_date and end_date are `datetime.date` objects
    # if isinstance(start_date, str):
    #     start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    # if isinstance(end_date, str):
    #     end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

    gral_graph_html = failed_responsibility_desambiguation_transport_vs_client(relativized_df, start_date, end_date, sellers_objects=sellers, transport=True)
    failed_graph_html = failed_responsibility_desambiguation_transport_vs_client(relativized_df, start_date, end_date, sellers_objects=sellers, transport=False)

    if req.user.role == CustomUser.CLIENT:
        usr_role = None
    else:
        usr_role = 1

    return render(req, "entregas_amba_failed.html", context={
        "gral_graph_html": gral_graph_html,
        "failed_graph_html": failed_graph_html,
        "companies": companies,
        "form": form,
        "usr_role": usr_role
    })


def entregas_interior(req):

    return render(req, "entregas_interior.html")


def entregas_interior_central_stats(req):

    form = FilterForm(req.POST or None)
    start_date, end_date, sellers = define_dates_and_sellers(req, form)

    if req.user.role == CustomUser.CLIENT:
        usr_role = None
    else:
        usr_role = 1

    delivery_interior_fields = [
        "pedido",
        "seller",
        "fechaDespacho",
        "fechaEntrega",
        "estadoLpn",
        "codigoPostal",
        "codigoPostal__localidad",
        "codigoPostal__partido",
        "codigoPostal__provincia",
        ]
    
    primary_df = query_primary_order_df_interior(req, sellers, start_date, end_date, delivery_interior_fields)
    print(primary_df)
    enriched_df = enrich_primary_df_timedeltas(primary_df, "fechaDespacho", "fechaEntrega")
    print(enriched_df)

    averages_by_localidad = enriched_df.groupby('codigoPostal__localidad')[['raw_delta_days', 'busy_delta_days']].mean().reset_index()
    averages_by_partido = enriched_df.groupby('codigoPostal__partido')[['raw_delta_days', 'busy_delta_days']].mean().reset_index()
    averages_by_provincia = enriched_df.groupby('codigoPostal__provincia')[['raw_delta_days', 'busy_delta_days']].mean().reset_index()

    localidad_graph = create_bar_chart(averages_by_localidad, 'codigoPostal__localidad', ['raw_delta_days', 'busy_delta_days'], "Averages by Localidad")
    partido_graph = create_bar_chart(averages_by_partido, 'codigoPostal__partido', ['raw_delta_days', 'busy_delta_days'], "Averages by Partido")
    provincia_graph = create_bar_chart(averages_by_provincia, 'codigoPostal__provincia', ['raw_delta_days', 'busy_delta_days'], "Averages by Provincia")

    return render(req, "entregas_interior_central_stats.html", context={
        "localidad_graph": localidad_graph,
        "partido_graph": partido_graph,
        "provincia_graph": provincia_graph,
        "form": form,
        "usr_role": usr_role
    })