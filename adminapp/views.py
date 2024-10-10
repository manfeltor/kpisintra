from django.shortcuts import render
import pandas as pd
import os
from usersapp.models import Company
from dataapp.models import Order
from .populateordermodelhelpers import parse_date
import json
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.decorators import login_required

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

        # Get the uploaded file (single file)
        uploaded_file = request.FILES['excel_file']

        # Save the uploaded file to a temporary location
        fs = FileSystemStorage()
        file_path = fs.save(uploaded_file.name, uploaded_file)
        status_messages.append(f"Processing {file_path}...")

        try:
            # Read the Excel file into a pandas DataFrame
            df = pd.read_excel(fs.path(file_path))

            # Iterate over the DataFrame rows and create Order objects
            for _, row in df.iterrows():
                try:
                    # Validate mandatory fields
                    pedido = row.get('pedido')
                    if not pedido:
                        raise ValueError("Missing 'pedido' in row")

                    # Get or create the Company based on the 'seller' field
                    seller_name = row['seller']
                    company, created = Company.objects.get_or_create(name=seller_name)

                    # Create the Order object
                    order = Order(
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
                    )
                    order.save()
                    successful_orders += 1

                except Exception as e:
                    failed_orders += 1
                    status_messages.append(f"Error saving order {pedido}: {e}")

        except Exception as e:
            status_messages.append(f"Error reading file: {e}")

        finally:
            # Clean up: Delete the file after processing
            fs.delete(file_path)

        # Final status messages
        status_messages.append(f"Processing complete: {successful_orders} orders saved, {failed_orders} errors encountered.")
        return render(request, 'process_orders.html', {'status_messages': status_messages})

    return render(request, 'process_orders.html')