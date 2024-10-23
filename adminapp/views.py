from django.shortcuts import render, redirect
import pandas as pd
from usersapp.models import Company
from dataapp.models import Order
from .populateordermodelhelpers import parse_date
import json
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse
import openpyxl
from io import BytesIO
from django.db import transaction
from django.contrib import messages

# Create your views here.
def adminpanel(req):
    return render(req, "admin_panel.html")

# POPULATE ORDER MODEL Main function to process Excel files and populate Order model
@login_required
def process_orders_from_upload(request):
    if request.method == 'POST' and request.FILES.get('excel_file'):
        status_messages = []
        successful_orders = 0
        failed_orders = 0
        batchzise = 1000

        # Get the uploaded file (single file)
        uploaded_file = request.FILES['excel_file']

        # Read the uploaded file into memory using BytesIO (works for both GCS and local)
        try:
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

                        seller_name = row['seller']
                        company, _ = Company.objects.get_or_create(name=seller_name)

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
                            order.trackingDistribucion = row.get('trackingDistribucion', '')
                            order.trackingTransporte = row.get('trackingTransporte', '')
                            order.codigoPostal = row['codigoPostal']
                            order.order_data = json.dumps({})  # Set to serialized empty JSON object
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
                                trackingDistribucion=row.get('trackingDistribucion', ''),
                                trackingTransporte=row.get('trackingTransporte', ''),
                                codigoPostal=row['codigoPostal'],
                                order_data=json.dumps({})  # Set to serialized empty JSON object
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

        except Exception as e:
            status_messages.append(f"Error reading file: {e}")

        status_messages.append(f"Processing complete: {successful_orders} orders saved, {failed_orders} errors encountered.")
        return render(request, 'admin_panel.html', {'status_messages': status_messages})

    return render(request, 'admin_panel.html')


def db_manager(req):
    return render(req, "db_manager.html")


def download_template_xlsx(request):
    # Create a new Excel workbook and sheet
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
            messages.success(request, "All orders have been successfully deleted.")
        except Exception as e:
            messages.error(request, f"Error occurred while deleting orders: {e}")
    return redirect('db_manager')