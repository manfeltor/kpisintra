from django.shortcuts import render
from .srtrackingDataProcessingFunctions import get_sr_tracking_summary, enrich_sr_tracking_summary
from .srtrackingDataProcessingFunctions import get_monthly_tracking_percentages
from django.utils.timezone import now
from .plotly_funcs import fallidos_vs_completados_graph, failed_responsibility_breakdown_graph
from .plotly_funcs import failed_responsibility_desambiguation_transport_vs_client, create_bar_chart
from .plotly_funcs import create_filtered_chart
# from django.core.exceptions import ValidationError
# from datetime import datetime, timedelta
from usersapp.models import Company, CustomUser
from .forms import FilterForm
from .main_functions import define_dates_and_sellers
from .orderDataProcessingFunctions import query_primary_order_df_interior, enrich_primary_df_timedeltas
from .orderDataProcessingFunctions import generate_frequency_df
# from .orderDataProcessingFunctions import calculate_weighted_averages_with_hierarchy, calculate_weighted_averages_higher_level


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
        
    # primary cleaning for calculations
    primary_df = query_primary_order_df_interior(req, sellers, start_date, end_date, delivery_interior_fields)
    # print(primary_df)
    enriched_df = enrich_primary_df_timedeltas(primary_df, "fechaDespacho", "fechaEntrega")
    # print(enriched_df)

    # raw averages
    averages_by_partido_localidad = enriched_df.groupby(['codigoPostal__partido', 'codigoPostal__localidad'])[['raw_delta_days', 'busy_delta_days']].mean().reset_index()
    averages_by_provincia_partido = enriched_df.groupby(['codigoPostal__provincia', 'codigoPostal__partido'])[['raw_delta_days', 'busy_delta_days']].mean().reset_index()
    averages_by_provincia = enriched_df.groupby('codigoPostal__provincia')[['raw_delta_days', 'busy_delta_days']].mean().reset_index()

    # weighted averages
    # weighted_averages_localidad = calculate_weighted_averages_with_hierarchy(
    # enriched_df=enriched_df,
    # heriarchy_col='codigoPostal__partido',
    # child_col='codigoPostal__localidad',
    # first_col='raw_delta_days',
    # second_col='busy_delta_days'
    # )
    # print(weighted_averages_localidad)
    # weighted_averages_partido = calculate_weighted_averages_with_hierarchy(
    # enriched_df=enriched_df,
    # heriarchy_col='codigoPostal__provincia',
    # child_col='codigoPostal__partido',
    # first_col='raw_delta_days',
    # second_col='busy_delta_days'
    # )
    # weighted_averages_provincia = calculate_weighted_averages_higher_level(
    # enriched_df=enriched_df,
    # group_col='codigoPostal__provincia',
    # first_col='raw_delta_days',
    # second_col='busy_delta_days'
    # )

    # raw graphs
    localidad_graph = create_filtered_chart(averages_by_partido_localidad, 'codigoPostal__partido', 'codigoPostal__localidad', ['raw_delta_days', 'busy_delta_days'], "Averages by Localidad and Partido")
    partido_graph = create_filtered_chart(averages_by_provincia_partido, 'codigoPostal__provincia', 'codigoPostal__partido', ['raw_delta_days', 'busy_delta_days'], "Averages by Partido")
    provincia_graph = create_bar_chart(averages_by_provincia, 'codigoPostal__provincia', ['raw_delta_days', 'busy_delta_days'], "Averages by Provincia")

    # weighted graphs
    # weighted_localidad_graph = create_filtered_chart(
    # df=weighted_averages_localidad,
    # group_col='codigoPostal__partido',
    # sub_group_col='codigoPostal__localidad',
    # y_col=['raw_delta_days_weighted', 'busy_delta_days_weighted'],
    # title="Weighted Averages by Localidad",
    # raws_col="raw_delta_days_weighted",
    # busy_col="busy_delta_days_weighted"
    # )
    # weighted_partido_graph = create_filtered_chart(
    # df=weighted_averages_partido,
    # group_col='codigoPostal__provincia',
    # sub_group_col='codigoPostal__partido',
    # y_col=['raw_delta_days_weighted', 'busy_delta_days_weighted'],
    # title="Weighted Averages by Partido",
    # raws_col="raw_delta_days_weighted",
    # busy_col="busy_delta_days_weighted"
    # )
    # weighted_provincia_graph = create_bar_chart(
    # df=weighted_averages_provincia,
    # group_col='codigoPostal__provincia',
    # y_col=['raw_delta_days_weighted', 'busy_delta_days_weighted'],
    # title="Weighted Averages by Provincia"
    # )

    return render(req, "entregas_interior_central_stats.html", context={
        # "weighted_localidad_graph": weighted_localidad_graph,
        # "weighted_partido_graph": weighted_partido_graph,
        # "weighted_provincia_graph": weighted_provincia_graph,
        "localidad_graph": localidad_graph,
        "partido_graph": partido_graph,
        "provincia_graph": provincia_graph,
        "form": form,
        "usr_role": usr_role
    })


def entregas_interior_descriptive_stats(req):
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
    
    # Prepare primary data
    primary_df = query_primary_order_df_interior(req, sellers, start_date, end_date, delivery_interior_fields)
    enriched_df = enrich_primary_df_timedeltas(primary_df, "fechaDespacho", "fechaEntrega")
    raw_df, busy_df = generate_frequency_df(enriched_df=enriched_df)
    
    
    return render(req, "entregas_interior_descriptive_stats.html", context={})