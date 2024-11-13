from django.shortcuts import render, redirect
import pandas as pd
from usersapp.models import Company
from dataapp.models import Order, PostalCodes, SRTrackingData, CATrackingData
from dataapp.populateordermodelhelpers import parse_date
import json
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse
import openpyxl
from io import BytesIO
from django.db import transaction
from django.contrib import messages
import traceback
import logging
from dataapp.srapihandler import process_tracking_data
import csv
import concurrent.futures

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create your views here.
def adminpanel(req):
    return render(req, "admin_panel.html")

def db_manager(req):
    return render(req, "db_manager.html")


# POPULATE ORDER MODEL Main function to process Excel files and populate Order model
def process_single_row(row, existing_lpns):
    """Process a single row of the DataFrame, returning an Order object to create or update."""
    try:
        pedido = row.get('pedido')
        if not pedido:
            raise ValueError("Missing 'pedido' in row")
        
        row_json = json.dumps(row.to_dict())
        seller_name = row['seller']
        company, _ = Company.objects.get_or_create(name=seller_name)

        # Process tracking data
        if row.get('trackingTransporte') not in ['', None]:
            tracking_transporte = row.get('trackingTransporte')
            tracking_transporte_data, _ = CATrackingData.objects.get_or_create(trackingTransporte=tracking_transporte)
        else:
            tracking_transporte_data = None

        postal_code_xlsx = str(int(row.get('codigoPostal')))
        postal_code_model = PostalCodes.objects.get(cp=postal_code_xlsx)

        if row['lpn'] in existing_lpns:
            # Update existing order
            order = Order.objects.get(lpn=row['lpn'])
            order.pedido = pedido
            order.flujo = row['flujo']
            order.seller = company
            order.sucursal = row['sucursal']
            order.estadoPedido = row['estadoPedido']
            order.fechaCreacion = parse_date(row['fechaCreacion'])
            order.fechaRecepcion = parse_date(row.get('fechaRecepcion', None))
            order.fechaDespacho = parse_date(row.get('fechaDespacho', None))
            order.fechaEntrega = parse_date(row.get('fechaEntrega', None))
            order.estadoLpn = row['estadoLpn']
            order.provincia = row['provincia']
            order.localidad = row['localidad']
            order.zona = row['zona']
            order.trackingDistribucion = row['trackingDistribucion']
            order.trackingTransporte = tracking_transporte_data
            order.codigoPostal = postal_code_model
            order.order_data = row_json
            return 'update', order
        else:
            # Create a new order
            new_order = Order(
                pedido=pedido,
                flujo=row['flujo'],
                seller=company,
                sucursal=row['sucursal'],
                estadoPedido=row['estadoPedido'],
                fechaCreacion=parse_date(row['fechaCreacion']),
                fechaRecepcion=parse_date(row.get('fechaRecepcion', None)),
                fechaDespacho=parse_date(row.get('fechaDespacho', None)),
                fechaEntrega=parse_date(row.get('fechaEntrega', None)),
                lpn=row['lpn'],
                estadoLpn=row['estadoLpn'],
                provincia=row['provincia'],
                localidad=row['localidad'],
                zona=row['zona'],
                trackingDistribucion=row['trackingDistribucion'],
                trackingTransporte=tracking_transporte_data,
                codigoPostal=postal_code_model,
                order_data=row_json
            )
            return 'create', new_order
    except Exception as e:
        # Log errors and return a failed entry
        print(f"Error processing row: {e}")
        return 'error', None

@login_required
def process_orders_from_upload(request):
    if request.method == 'POST' and request.FILES.get('oms_excel_file'):
        successful_orders = 0
        failed_orders = 0
        batch_size = 1000

        uploaded_file = request.FILES['oms_excel_file']
        if not uploaded_file.name.endswith(('.xlsx', '.xls')):
            messages.error(request, 'Formato de archivo no soportado. Asegurese que esta subiendo un xlsx.')
            return render(request, 'db_manager.html')

        df = pd.read_excel(BytesIO(uploaded_file.read()))

        # Get all existing LPNs to check for duplicates
        existing_lpns = set(Order.objects.filter(lpn__in=df['lpn']).values_list('lpn', flat=True))

        # Prepare lists to collect results for bulk operations
        orders_to_create = []
        orders_to_update = []

        # Process rows concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(process_single_row, row, existing_lpns) for _, row in df.iterrows()]

            for future in concurrent.futures.as_completed(futures):
                result_type, order = future.result()
                if result_type == 'create':
                    orders_to_create.append(order)
                    successful_orders += 1
                elif result_type == 'update':
                    orders_to_update.append(order)
                    successful_orders += 1
                else:
                    failed_orders += 1

        # Perform bulk create and update after processing
        with transaction.atomic():
            Order.objects.bulk_create(orders_to_create, batch_size=batch_size)
            Order.objects.bulk_update(orders_to_update, fields=[
                'pedido', 'flujo', 'seller', 'sucursal', 'estadoPedido', 'fechaCreacion',
                'fechaRecepcion', 'fechaDespacho', 'fechaEntrega', 'estadoLpn', 'provincia',
                'localidad', 'zona', 'trackingDistribucion', 'trackingTransporte', 'codigoPostal', 'order_data'
            ], batch_size=batch_size)

        messages.success(request, f"Procesamiento completo: {successful_orders} ordenes guardadas, {failed_orders} ordenes fallidas.")
        return render(request, 'db_manager.html')
    
    return render(request, 'db_manager.html')
    

def download_template_xlsx(request):
    # Create a new Excel workbook and sheet for oms submissions
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Template"

    # Define the column headers
    headers = [
        "pedido", "flujo", "seller", "sucursal", "estadoPedido",
        "fechaCreacion", "fechaRecepcion", "fechaDespacho", "fechaEntrega",
        "lpn", "estadoLpn", "provincia", "localidad", "zona",
        "trackingDistribucion", "trackingTransporte", "codigoPostal"
    ]

    # Add the headers to the first row of the sheet
    ws.append(headers)

    # Save the workbook to a BytesIO object (in memory)
    with BytesIO() as buffer:
        wb.save(buffer)
        buffer.seek(0)  # Rewind the buffer

        # Create the response and send the file for download
        response = HttpResponse(buffer, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename=template_oms.xlsx'
        return response
    
    
@staff_member_required
def delete_all_orders(request):
    if request.method == "POST":
        try:
            Order.objects.all().delete()
            messages.success(request, "Todas las ordenes fueron eliminadas con exito.")
        except Exception as e:
            messages.error(request, f"Ocurrio un eeror durante el proceso: {e}")
    return redirect('db_manager')


@login_required
@staff_member_required
def upload_postal_codes(request):
    if request.method == 'POST' and request.FILES.get('cp_excel_file'):
        successful_inserts = 0
        failed_inserts = 0
        batch_size = 1000

        # Get the uploaded file (single file)

        # Read the uploaded file into memory using BytesIO (works for both GCS and local)
        try:
            uploaded_file = request.FILES['cp_excel_file']
            excel_file = uploaded_file.read()
            excel_io = BytesIO(excel_file)

            # Validate if the file is an actual Excel file
            try:
                df = pd.read_excel(excel_io)
            except Exception as e:
                messages.error(request, f"El archivo subido no es válido. Asegúrese de que es un archivo Excel. Error: {str(e)}")
                return render(request, 'db_manager.html')

            # Ensure that required columns exist
            required_columns = ['cp', 'localidad', 'partido', 'provincia', 'region', 'distrito', 'amba_intralog', 'flex']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                messages.error(request, f"Faltan las siguientes columnas obligatorias en el archivo: {', '.join(missing_columns)}")
                return render(request, 'db_manager.html')

            postal_codes_to_create = []
            postal_codes_to_update = []

            # Gather all postal codes to check for existing ones
            existing_cps = set(PostalCodes.objects.filter(cp__in=df['cp']).values_list('cp', flat=True))

            with transaction.atomic():
                for _, row in df.iterrows():
                    try:
                        # Check if the postal code already exists
                        if row['cp'] in existing_cps:
                            # Update existing postal code
                            postal_code = PostalCodes.objects.get(cp=row['cp'])
                            postal_code.localidad = row['localidad']
                            postal_code.partido = row['partido']
                            postal_code.provincia = row['provincia']
                            postal_code.region = row['region']
                            postal_code.distrito = row['distrito']
                            postal_code.amba_intralog = row['amba_intralog']
                            postal_code.flex = row['flex']
                            postal_code.dias_limite = row['dias_limite']
                            postal_codes_to_update.append(postal_code)
                        else:
                            # Create a new postal code entry
                            postal_codes_to_create.append(PostalCodes(
                                cp=row['cp'],
                                localidad=row['localidad'],
                                partido=row['partido'],
                                provincia=row['provincia'],
                                region=row['region'],
                                distrito=row['distrito'],
                                amba_intralog=row['amba_intralog'],
                                flex=row['flex'],
                                dias_limite=row['dias_limite']
                            ))
                        successful_inserts += 1
                    except Exception as e:
                        failed_inserts += 1
                        # Log detailed error if needed
                        print(f"Error processing row {row['cp']}: {e}")

            # Bulk create and update postal codes
            PostalCodes.objects.bulk_create(postal_codes_to_create, batch_size=batch_size)
            PostalCodes.objects.bulk_update(postal_codes_to_update, [
                'localidad', 'partido', 'provincia', 'region', 'distrito', 'amba_intralog', 'flex', 'dias_limite'
            ], batch_size=batch_size)

            messages.success(request, f"Procesamiento completo: {successful_inserts} cps procesados, {failed_inserts} inserciones fallidas.")

        except Exception as e:
            tb = traceback.format_exc()
            messages.error(request, f"Error procesando el archivo: {e}, trace: {tb}")
            return render(request, 'db_manager.html')
        
        return render(request, 'db_manager.html')
    print(request.FILES)
    return render(request, 'db_manager.html')


def download_cp_template_xlsx(request):
    # Create a new Excel workbook and sheet for oms submissions
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Template"

    # Define the column headers
    headers = [
        "cp", "localidad", "partido", "provincia", "region",
        "distrito", "amba_intralog", "flex", "dias_limite"
    ]

    # Add the headers to the first row of the sheet
    ws.append(headers)

    # Save the workbook to a BytesIO object (in memory)
    with BytesIO() as buffer:
        wb.save(buffer)
        buffer.seek(0)  # Rewind the buffer

        # Create the response and send the file for download
        response = HttpResponse(buffer, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename=template_cp.xlsx'
        return response
    

@staff_member_required
def delete_all_orders_cp(request):
    if request.method == "POST":
        try:
            PostalCodes.objects.all().delete()
            messages.success(request, "Todos los registros han sido eliminados correctamente.")
        except Exception as e:
            messages.error(request, f"Ocurrio un error en el proceso: {e}")
    return redirect('db_manager')


@staff_member_required
def SR_api_ingestion_populate(request):
    process_tracking_data(request, update_mode=False)
    for handler in logger.handlers:
        if hasattr(handler, 'buffer'):
            for record in handler.buffer:
                if record.levelname == "INFO":
                    messages.info(request, record.getMessage())
                elif record.levelname == "ERROR":
                    messages.error(request, record.getMessage())
            handler.flush()

    return redirect('db_manager')


@staff_member_required
def SR_api_ingestion_update(request):
    process_tracking_data(request, update_mode=True)
    for handler in logger.handlers:
        if hasattr(handler, 'buffer'):
            for record in handler.buffer:
                if record.levelname == "INFO":
                    messages.info(request, record.getMessage())
                elif record.levelname == "ERROR":
                    messages.error(request, record.getMessage())
            handler.flush()

    return redirect('db_manager')


@staff_member_required
def delete_all_SRdata(request):
    if request.method == "POST":
        try:
            SRTrackingData.objects.all().delete()
            messages.success(request, "Toda la data de los trackings de SR fue eliminada con exito.")
        except Exception as e:
            messages.error(request, f"Ocurrio un eeror durante el proceso: {e}")
    return redirect('db_manager')


@staff_member_required
def export_srtrackingdata_to_csv(request):
    # Create the HttpResponse object with CSV headers.
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="sr_tracking_data.csv"'

    writer = csv.writer(response)
    # Write the header row based on your model's fields
    writer.writerow([
        'tracking_id', 'status', 'title', 'tipo', 'pedido', 'seller', 
        'reference', 'checkout_observation', 'planned_date', 'rawJson'
    ])

    # Write data rows from the SRTrackingData model
    for record in SRTrackingData.objects.all():
        writer.writerow([
            record.tracking_id,
            record.status,
            record.title,
            record.tipo,
            record.pedido,
            record.seller,
            record.reference,
            record.checkout_observation,
            record.planned_date,
            record.rawJson
        ])

    return response