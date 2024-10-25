from django.shortcuts import render, redirect
import pandas as pd
from usersapp.models import Company
from dataapp.models import Order, PostalCodes, SRTrackingData
from .populateordermodelhelpers import parse_date
import json
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse
import openpyxl
from io import BytesIO
from django.db import transaction
from django.contrib import messages
import traceback

# Create your views here.
def adminpanel(req):
    return render(req, "admin_panel.html")

def db_manager(req):
    return render(req, "db_manager.html")


# POPULATE ORDER MODEL Main function to process Excel files and populate Order model
@login_required
def process_orders_from_upload(request):
    if request.method == 'POST' and request.FILES.get('oms_excel_file'):
        status_messages = []
        successful_orders = 0
        failed_orders = 0
        batchzise = 1000

        # Get the uploaded file (single file)
        # uploaded_file = request.FILES['excel_file']

        # Read the uploaded file into memory using BytesIO (works for both GCS and local)
        try:
            uploaded_file = request.FILES['oms_excel_file']

            # Ensure the uploaded file is an Excel file
            if not uploaded_file.name.endswith(('.xlsx', '.xls')):
                raise ValueError('Formato de archivo no soportado. Asegurese que esta subiendo un xlsx.')
            excel_file = uploaded_file.read()
            excel_io = BytesIO(excel_file)
            df = pd.read_excel(excel_io)

            orders_to_create = []
            orders_to_update = []

            # Gather all LPNs to check for existing ones
            existing_lpns = set(Order.objects.filter(lpn__in=df['lpn']).values_list('lpn', flat=True))

            with transaction.atomic():
                for _, row in df.iterrows():
                    try:
                        pedido = row.get('pedido')
                        if not pedido:
                            raise ValueError("Missing 'pedido' in row")
                        
                        row_json = json.dumps(row.to_dict())

                        seller_name = row['seller']
                        company, _ = Company.objects.get_or_create(name=seller_name)

                        if row.get('trackingDistribucion') not in ['', None]:
                            tracking_distribucion = row.get('trackingDistribucion')
                            tracking_data, created = SRTrackingData.objects.get_or_create(
                                trackingDistribucion=tracking_distribucion
                            )
        
                        postal_code_xlsx = row.get('codigoPostal')
                        try:
                            postal_code_model = PostalCodes.objects.get(cp=postal_code_xlsx)
                        except PostalCodes.DoesNotExist:
                            raise ValueError(f"Postal code {postal_code_xlsx} not found in PostalCodes database.")

                        # Check if the order with this LPN already exists
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
                            order.trackingDistribucion = tracking_data
                            order.trackingTransporte = row.get('trackingTransporte', '')
                            order.codigoPostal = postal_code_model
                            order.order_data = row_json
                            orders_to_update.append(order)
                        else:
                            # Create a new order
                            orders_to_create.append(Order(
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
                                trackingDistribucion=tracking_data,
                                trackingTransporte=row.get('trackingTransporte', ''),
                                codigoPostal=postal_code_model,
                                order_data=row_json
                            ))
                        successful_orders += 1
                    except Exception as e:
                        failed_orders += 1
                        status_messages.append(f"Error processing row: {e}")

            # Bulk create and update orders
            Order.objects.bulk_create(orders_to_create, batch_size=batchzise)
            Order.objects.bulk_update(orders_to_update, [
                'pedido', 'flujo', 'seller', 'sucursal', 'estadoPedido', 'fechaCreacion',
                'fechaRecepcion', 'fechaDespacho', 'fechaEntrega', 'estadoLpn', 'provincia',
                'localidad', 'zona', 'trackingDistribucion', 'trackingTransporte', 'codigoPostal', 'order_data'
            ], batch_size=batchzise)

            messages.success(request, f"Procesamiento completo: {successful_orders} ordenes guardadas, {failed_orders} ordenes fallidas.")

        
        except Exception as e:
            tb = traceback.format_exc()
            messages.error(request, f"Error reading file: {e} trace: {tb}")
            

        # status_messages.append(f"Processing complete: {successful_orders} orders saved, {failed_orders} errors encountered.")
        # messages.success(request, f"Processing complete: {successful_orders} orders saved, {failed_orders} errors encountered.")

        return render(request, 'db_manager.html')
        # return JsonResponse({'message': 'File uploaded successfully', 'success': True})

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