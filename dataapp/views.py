from django.shortcuts import render
from .srtrackingDataProcessingFunctions import get_sr_tracking_summary, enrich_sr_tracking_summary
from .srtrackingDataProcessingFunctions import get_monthly_tracking_percentages
from .plotly_funcs import fallidos_vs_completados_graph, failed_responsibility_breakdown_graph
from .plotly_funcs import failed_responsibility_desambiguation_transport_vs_client, create_bar_chart
from .plotly_funcs import create_filtered_chart, plot_cumulative_percentage, plot_box_plots, plot_relative_volume_bar
from .plotly_funcs import plot_tipo_percentage_bar_chart
from usersapp.models import Company, CustomUser
from .forms import FilterForm
from .main_functions import define_dates_and_sellers, add_cumulative_percentage, add_relative_percentage
from .main_functions import adjusted_calculate_percentages, percentage_strip
from .orderDataProcessingFunctions import query_primary_order_df_interior, enrich_primary_df_timedeltas
from .orderDataProcessingFunctions import generate_frequency_df
from io import BytesIO
import pandas as pd
from django.http import HttpResponse
from django.utils.timezone import now
from datetime import datetime, timedelta
from django.contrib import messages

def entregas_panel(req):
    return render(req, "kpisentregas.html")


def entregas_amba(req):
    
    return render(req, "entregas_amba.html")


def entregas_amba_gral(req):

    companies = Company.objects.all()

    form = FilterForm(req.POST or None)

    start_date, end_date, sellers = define_dates_and_sellers(req, form)

    if req.user.role == CustomUser.CLIENT:
        usr_role = None
    else:
        usr_role = 1

    df_query = get_sr_tracking_summary(req, sellers, False, start_date, end_date)
    if df_query.empty:
            messages.warning(req, "No hay data disponible para las fechas filtradas.")
            return render(req, "entregas_amba_gral.html", context={
                "form": form,
                "companies": companies,
                "usr_role": usr_role,
            })   
    df_translated = enrich_sr_tracking_summary(df_query)
    relativized_df = get_monthly_tracking_percentages(df_translated, "responsibility")

    gral_graph_html = fallidos_vs_completados_graph(relativized_df, start_date, end_date, sellers)
    failed_graph_html = failed_responsibility_breakdown_graph(relativized_df, start_date, end_date, sellers)

    for field, errors in form.errors.items():
        for error in errors:
            messages.error(req, f"{field}: {error}")

    return render(req, "entregas_amba_gral.html", context={
        "gral_graph_html": gral_graph_html,
        "failed_graph_html": failed_graph_html,
        "companies": companies,
        "form": form,
        "usr_role": usr_role
    })


def download_entregas_amba_gral(req):

    form = FilterForm(req.POST or None)

    if req.user.role == CustomUser.CLIENT:
        usr_role = None
    else:
        usr_role = 1

    start_date = req.GET.get('start_date')
    if start_date == 'None' or not start_date:
        start_date = None

    end_date = req.GET.get('end_date')
    if end_date == 'None' or not end_date:
        end_date = None

    if not usr_role:
        sellers = req.GET.getlist('sellers')
        if not sellers:
            sellers = None
    else:
        sellers = [req.user.company]


    # Fetch and process the data
    df_query = get_sr_tracking_summary(req, sellers, False, start_date, end_date)
    if df_query.empty:
            messages.warning(req, "No hay data disponible para las fechas filtradas.")
            return render(req, "entregas_amba_gral.html", context={
                "form": form,
                "usr_role": usr_role,
            }) 
    df_translated = enrich_sr_tracking_summary(df_query)
    relativized_df = get_monthly_tracking_percentages(df_translated, "responsibility")
    relativized_df.drop(columns='total_count', inplace=True)

    # Prepare the output
    output = BytesIO()

    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Write the main data
        relativized_df.to_excel(writer, index=False, sheet_name='responsibility_matrix')

        # Add a sheet for filters
        filter_summary = {
            'Filter': ['Start Date', 'End Date', 'Selected Sellers'],
            'Value': [start_date or 'Not Applied', end_date or 'Not Applied', ', '.join(sellers) if sellers else 'All Sellers']
        }
        filter_df = pd.DataFrame(filter_summary)
        filter_df.to_excel(writer, index=False, sheet_name='filters')

    output.seek(0)

    # Prepare the response
    response = HttpResponse(
        output,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="responsibility_matrix.xlsx"'

    return response


def entregas_amba_failed(req):

    companies = Company.objects.all()

    form = FilterForm(req.POST or None)

    start_date, end_date, sellers = define_dates_and_sellers(req, form)

    if req.user.role == CustomUser.CLIENT:
        usr_role = None
    else:
        usr_role = 1

    df_query = get_sr_tracking_summary(req, sellers, failed=False, start_date=start_date, end_date=end_date)
    if df_query.empty:
            messages.warning(req, "No hay data disponible para las fechas filtradas.")
            return render(req, "entregas_amba_failed.html.html", context={
                "form": form,
                "usr_role": usr_role,
            })
    df_translated = enrich_sr_tracking_summary(df_query)
    relativized_df = get_monthly_tracking_percentages(df_translated, 'label')

    gral_graph_html = failed_responsibility_desambiguation_transport_vs_client(relativized_df, start_date, end_date, sellers_objects=sellers, transport=True)
    failed_graph_html = failed_responsibility_desambiguation_transport_vs_client(relativized_df, start_date, end_date, sellers_objects=sellers, transport=False)

    return render(req, "entregas_amba_failed.html", context={
        "gral_graph_html": gral_graph_html,
        "failed_graph_html": failed_graph_html,
        "companies": companies,
        "form": form,
        "usr_role": usr_role
    })


def download_entregas_amba_failed(req):

    form = FilterForm(req.POST or None)

    if req.user.role == CustomUser.CLIENT:
        usr_role = None
    else:
        usr_role = 1

    start_date = req.GET.get('start_date')
    if start_date == 'None' or not start_date:
        start_date = None

    end_date = req.GET.get('end_date')
    if end_date == 'None' or not end_date:
        end_date = None

    if not usr_role:
        sellers = req.GET.getlist('sellers')
        if not sellers:
            sellers = None
    else:
        sellers = [req.user.company]

    # Fetch and process the data
    df_query = get_sr_tracking_summary(req, sellers, True, start_date, end_date)
    if df_query.empty:
            messages.warning(req, "No hay data disponible para las fechas filtradas.")
            return render(req, "entregas_amba_failed.html.html", context={
                "form": form,
                "usr_role": usr_role,
            })
    df_translated = enrich_sr_tracking_summary(df_query)
    relativized_df = get_monthly_tracking_percentages(df_translated, "label")
    relativized_df.drop(columns='total_count', inplace=True)

    # Prepare the output
    output = BytesIO()

    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Write the main data
        relativized_df.to_excel(writer, index=False, sheet_name='responsibility_matrix')

        # Add a sheet for filters
        filter_summary = {
            'Filter': ['Start Date', 'End Date', 'Selected Sellers'],
            'Value': [start_date or 'Not Applied', end_date or 'Not Applied', ', '.join(sellers) if sellers else 'All Sellers']
        }
        filter_df = pd.DataFrame(filter_summary)
        filter_df.to_excel(writer, index=False, sheet_name='filters')

    output.seek(0)

    # Prepare the response
    response = HttpResponse(
        output,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="failed_matrix.xlsx"'

    return response


def entregas_amba_descr(req):

    companies = Company.objects.all()

    form = FilterForm(req.POST or None)

    start_date, end_date, sellers = define_dates_and_sellers(req, form)

    delivery_amba_fields = [
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
    
    primary_df = query_primary_order_df_interior(req, sellers, start_date, end_date, delivery_amba_fields, True)
    if primary_df.empty:
            messages.warning(req, "No hay data disponible para las fechas filtradas.")
            return render(req, "entregas_amba_zone.html", context={
                "form": form,
                "usr_role": usr_role,
            })

    # volume partido graph
    grouped_volume_partido_df = primary_df.groupby("codigoPostal__partido", as_index=False)["pedido"].count()
    grouped_relativized_volume_partido_df = add_relative_percentage(grouped_volume_partido_df, "pedido")
    # partido_volume_graph = plot_relative_volume_bar(grouped_volume_partido_df, "codigoPostal__partido", )

    # volume localidad graph
    grouped_volume_localidad_df = primary_df.groupby(["codigoPostal__localidad", "codigoPostal__partido"], as_index=False)["pedido"].count()
    grouped_volume_localidad_df['percentage'] = grouped_volume_localidad_df.groupby('codigoPostal__partido')['pedido'].transform(lambda x: (x / x.sum()) * 100)
    filtered_df = grouped_volume_localidad_df[grouped_volume_localidad_df['codigoPostal__localidad'] == 'CIUDAD AUTONOMA DE BUENOS AIRES']

    if req.user.role == CustomUser.CLIENT:
        usr_role = None
    else:
        usr_role = 1
    
    return render(req, "entregas_amba_zone.html", context={
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
    if primary_df.empty:
            messages.warning(req, "No hay data disponible para las fechas filtradas.")
            return render(req, "entregas_interior_central_stats.html", context={
                "form": form,
                "usr_role": usr_role,
            })
    enriched_df0 = enrich_primary_df_timedeltas(primary_df, "fechaDespacho", "fechaEntrega")

    enriched_df = percentage_strip(enriched_df0, 'raw_delta_days', 0.60, True, True)
    print(enriched_df)

    # raw averages
    averages_by_partido_localidad = enriched_df.groupby(['codigoPostal__partido', 'codigoPostal__localidad'])[['raw_delta_days', 'busy_delta_days']].mean().reset_index()
    averages_by_provincia_partido = enriched_df.groupby(['codigoPostal__provincia', 'codigoPostal__partido'])[['raw_delta_days', 'busy_delta_days']].mean().reset_index()
    averages_by_provincia = enriched_df.groupby('codigoPostal__provincia')[['raw_delta_days', 'busy_delta_days']].mean().reset_index()

    # raw graphs
    localidad_graph = create_filtered_chart(averages_by_partido_localidad, 'codigoPostal__partido', 'codigoPostal__localidad', ['raw_delta_days', 'busy_delta_days'], "Promedios por Localidad y Partido")
    partido_graph = create_filtered_chart(averages_by_provincia_partido, 'codigoPostal__provincia', 'codigoPostal__partido', ['raw_delta_days', 'busy_delta_days'], "Promedios por partido")
    provincia_graph = create_bar_chart(averages_by_provincia, 'codigoPostal__provincia', ['raw_delta_days', 'busy_delta_days'], "Promedios por provincia")

    return render(req, "entregas_interior_central_stats.html", context={
        "localidad_graph": localidad_graph,
        "partido_graph": partido_graph,
        "provincia_graph": provincia_graph,
        "form": form,
        "usr_role": usr_role
    })


def download_entregas_interior_central_stats(req):

    form = FilterForm(req.POST or None)

    cutoff_date = now().date().replace(day=1) - timedelta(days=395)
    
    if req.user.role == CustomUser.CLIENT:
        usr_role = None
    else:
        usr_role = 1

    start_date0 = req.GET.get('start_date')
    if start_date0 == 'None' or not start_date0:
        start_date = cutoff_date

    end_date0 = req.GET.get('end_date')
    if end_date0 == 'None' or not end_date0:
        end_date = now().replace(tzinfo=None)

    if not usr_role:
        sellers = req.GET.getlist('sellers')
        if not sellers:
            sellers = None
    else:
        sellers = [req.user.company]

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
    if primary_df.empty:
            messages.warning(req, "No hay data disponible para las fechas filtradas.")
            return render(req, "entregas_interior_central_stats.html", context={
                "form": form,
                "usr_role": usr_role,
            })
    enriched_df = enrich_primary_df_timedeltas(primary_df, "fechaDespacho", "fechaEntrega")

    # raw averages
    averages_by_partido_localidad = enriched_df.groupby(['codigoPostal__partido', 'codigoPostal__localidad'])[['raw_delta_days', 'busy_delta_days']].mean().reset_index()
    averages_by_provincia_partido = enriched_df.groupby(['codigoPostal__provincia', 'codigoPostal__partido'])[['raw_delta_days', 'busy_delta_days']].mean().reset_index()
    averages_by_provincia = enriched_df.groupby('codigoPostal__provincia')[['raw_delta_days', 'busy_delta_days']].mean().reset_index()

    output = BytesIO()

    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:

        averages_by_partido_localidad.to_excel(writer, index=False, sheet_name='averages_by_partido_localidad')
        averages_by_provincia_partido.to_excel(writer, index=False, sheet_name='averages_by_provincia_partido')
        averages_by_provincia.to_excel(writer, index=False, sheet_name='averages_by_provincia')

        filter_summary = {
            'Filter': ['Start Date', 'End Date', 'Selected Sellers'],
            'Value': [start_date or 'Not Applied', end_date or 'Not Applied', ', '.join(sellers) if sellers else 'All Sellers']
        }
        filter_df = pd.DataFrame(filter_summary)
        filter_df.to_excel(writer, index=False, sheet_name='filters')

    output.seek(0)

    # Prepare the response
    response = HttpResponse(
        output,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="zonal_averages_matrix.xlsx"'

    return response



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
        "tipo",
        "fechaDespacho",
        "fechaEntrega",
        "estadoLpn",
        "codigoPostal",
        "codigoPostal__localidad",
        "codigoPostal__partido",
        "codigoPostal__provincia",
    ]
    
    # Prepare primary data
    primary_df0 = query_primary_order_df_interior(req, sellers, start_date, end_date, delivery_interior_fields, False, True)
    if primary_df0.empty:
            messages.warning(req, "No hay data disponible para las fechas filtradas.")
            return render(req, "entregas_interior_descriptive_stats.html", context={
                "form": form,
                "usr_role": usr_role,
            })
    primary_df = primary_df0[primary_df0['tipo'] != 'SUCA']
    enriched_df = enrich_primary_df_timedeltas(primary_df, "fechaDespacho", "fechaEntrega")
    
    # density graph
    raw_df_dens, busy_df_dens = generate_frequency_df(enriched_df=enriched_df, strip_percentage=0.065)
    raw_cumulative_df = add_cumulative_percentage(raw_df_dens, 'raw_delta_days', 'frequency')
    busy_cumulative_df = add_cumulative_percentage(busy_df_dens, 'busy_delta_days', 'frequency')
    density_graph = plot_cumulative_percentage(raw_cumulative_df, 'raw_delta_days', busy_cumulative_df, 'busy_delta_days')

    # box plot
    raw_df_box, busy_df_box = generate_frequency_df(enriched_df=enriched_df, grouped_df=False, strip_percentage=0.065)
    raw_grouped_df = raw_df_box.groupby("raw_delta_days", as_index=False)["frequency"].mean()
    busy_grouped_df = busy_df_box.groupby("busy_delta_days", as_index=False)["frequency"].mean()
    box_plot = plot_box_plots(raw_grouped_df, "raw_delta_days", busy_grouped_df, "busy_delta_days")

    # volume plot
    grouped_vol_df = enriched_df.groupby("codigoPostal__provincia", as_index=False)["pedido"].count()
    grouped_relative_vol_df = add_relative_percentage(grouped_vol_df, "pedido")
    volume_plot = plot_relative_volume_bar(grouped_relative_vol_df, "codigoPostal__provincia", "relative_percentage")

    # SUCA volume plot
    grouped_vol_SUCA_df0 = primary_df0.groupby(["codigoPostal__provincia", "tipo"], as_index=False)["pedido"].count()
    adjustment_factors = {'DIST': 0.93, 'SUCA': 1.07}
    grouped_vol_SUCA_df1 = adjusted_calculate_percentages(
        grouped_vol_SUCA_df0,
        group_col='codigoPostal__provincia',
        tipo_col='tipo',
        frequency_col='pedido',
        adjustment_factors=adjustment_factors
    )
    # grouped_vol_SUCA_df['percentage'] = grouped_vol_SUCA_df.groupby('codigoPostal__provincia')['pedido'].transform(lambda x: (x / x.sum()) * 100)
    grouped_vol_SUCA_df = grouped_vol_SUCA_df1.sort_values(by="percentage", ascending=True)
    SUCA_vol_graph = plot_tipo_percentage_bar_chart(grouped_vol_SUCA_df, "codigoPostal__provincia", "tipo", "percentage")
    
    return render(req, "entregas_interior_descriptive_stats.html",
                context={
                    "density_graph": density_graph,
                    "box_plot": box_plot,
                    "volume_plot": volume_plot,
                    "suca_vol_graph": SUCA_vol_graph,
                    "form": form,
                    "usr_role": usr_role,
                    }
                )


def download_entregas_interior_descriptive_stats(req):

    form = FilterForm(req.POST or None)

    cutoff_date = now().date().replace(day=1) - timedelta(days=395)
    
    if req.user.role == CustomUser.CLIENT:
        usr_role = None
    else:
        usr_role = 1

    start_date0 = req.GET.get('start_date')
    if start_date0 == 'None' or not start_date0:
        start_date = cutoff_date

    end_date0 = req.GET.get('end_date')
    if end_date0 == 'None' or not end_date0:
        end_date = now().replace(tzinfo=None)

    if not usr_role:
        sellers = req.GET.getlist('sellers')
        if not sellers:
            sellers = None
    else:
        sellers = [req.user.company]

    delivery_interior_fields = [
        "pedido",
        "seller",
        "tipo",
        "fechaDespacho",
        "fechaEntrega",
        "estadoLpn",
        "codigoPostal",
        "codigoPostal__localidad",
        "codigoPostal__partido",
        "codigoPostal__provincia",
    ]
        
    primary_df0 = query_primary_order_df_interior(req, sellers, start_date, end_date, delivery_interior_fields, False, True)
    if primary_df0.empty:
            messages.warning(req, "No hay data disponible para las fechas filtradas.")
            return render(req, "entregas_interior_descriptive_stats.html", context={
                "form": form,
                "usr_role": usr_role,
            })
    primary_df = primary_df0[primary_df0['tipo'] != 'SUCA']
    enriched_df = enrich_primary_df_timedeltas(primary_df, "fechaDespacho", "fechaEntrega")
    
    # density graph
    raw_df_dens, busy_df_dens = generate_frequency_df(enriched_df=enriched_df, strip_percentage=0.065)
    raw_cumulative_df = add_cumulative_percentage(raw_df_dens, 'raw_delta_days', 'frequency')
    busy_cumulative_df = add_cumulative_percentage(busy_df_dens, 'busy_delta_days', 'frequency')
    raw_cumulative_df.drop(columns=['frequency', 'cumulative'], inplace=True)
    busy_cumulative_df.drop(columns=['frequency', 'cumulative'], inplace=True)

    # box plot
    raw_df_box, busy_df_box = generate_frequency_df(enriched_df=enriched_df, grouped_df=False, strip_percentage=0.065)
    raw_grouped_df0 = raw_df_box.groupby("raw_delta_days", as_index=False)["frequency"].mean()
    raw_grouped_df1 = add_relative_percentage(raw_grouped_df0, "frequency")
    raw_grouped_df1.drop(columns='frequency', inplace=True)
    raw_grouped_df = raw_grouped_df1.sort_values(by='raw_delta_days', ascending=True)
    busy_grouped_df0 = busy_df_box.groupby("busy_delta_days", as_index=False)["frequency"].mean()
    busy_grouped_df1 = add_relative_percentage(busy_grouped_df0, "frequency")
    busy_grouped_df1.drop(columns='frequency', inplace=True)
    busy_grouped_df = busy_grouped_df1.sort_values(by='busy_delta_days', ascending=True)

    # volume plot
    grouped_vol_df = enriched_df.groupby("codigoPostal__provincia", as_index=False)["pedido"].count()
    grouped_relative_vol_df = add_relative_percentage(grouped_vol_df, "pedido")
    grouped_relative_vol_df.drop(columns='pedido', inplace=True)

    # SUCA volume plot
    grouped_vol_SUCA_df0 = primary_df0.groupby(["codigoPostal__provincia", "tipo"], as_index=False)["pedido"].count()
    adjustment_factors = {'DIST': 0.93, 'SUCA': 1.07}
    grouped_vol_SUCA_df = adjusted_calculate_percentages(
        grouped_vol_SUCA_df0,
        group_col='codigoPostal__provincia',
        tipo_col='tipo',
        frequency_col='pedido',
        adjustment_factors=adjustment_factors
    )
    # grouped_vol_SUCA_df['percentage'] = grouped_vol_SUCA_df.groupby('codigoPostal__provincia')['pedido'].transform(lambda x: (x / x.sum()) * 100)
    grouped_vol_SUCA_df.drop(columns='pedido', inplace=True)


    output = BytesIO()

    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:

        busy_cumulative_df.to_excel(writer, index=False, sheet_name='busy_cumulative_df')
        raw_cumulative_df.to_excel(writer, index=False, sheet_name='raw_cumulative_df')
        busy_grouped_df.to_excel(writer, index=False, sheet_name='busy_grouped_df')
        raw_grouped_df.to_excel(writer, index=False, sheet_name='raw_grouped_df')
        grouped_relative_vol_df.to_excel(writer, index=False, sheet_name='grouped_relative_vol_df')
        grouped_vol_SUCA_df.to_excel(writer, index=False, sheet_name='grouped_vol_SUCA_df')

        filter_summary = {
            'Filter': ['Start Date', 'End Date', 'Selected Sellers'],
            'Value': [start_date or 'Not Applied', end_date or 'Not Applied', ', '.join(sellers) if sellers else 'All Sellers']
        }
        filter_df = pd.DataFrame(filter_summary)
        filter_df.to_excel(writer, index=False, sheet_name='filters')

    output.seek(0)

    # Prepare the response
    response = HttpResponse(
        output,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="interior_descriptive_matrix.xlsx"'

    return response