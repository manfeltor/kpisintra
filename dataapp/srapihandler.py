import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from django.db import IntegrityError
from django.utils import timezone
from django.contrib import messages
from dataapp.models import SRTrackingData, Order
import logging
from decouple import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_data_for_date(request, planned_date):
    url = f"https://api.simpliroute.com/v1/routes/visits/?planned_date={planned_date}"
    SR_AUTH_TOKEN = config('SR_AUTH_TOKEN')
    headers = {
        "authorization": SR_AUTH_TOKEN,
        "content-type": "application/json"
    }
    
    for attempt in range(3):
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                return response.json()
            else:
                messages.error(request, f"Failed to fetch data for {planned_date}: {response.status_code}")
        except requests.RequestException as e:
            messages.error(request, f"Error on attempt {attempt+1} for date {planned_date}: {e}")
        time.sleep(0.2)
    return None

def parse_and_save_data(request, data):
    tracking_entries = []
    for entry in data:
        try:
            # Extract fields
            tracking_id = entry.get("tracking_id")
            status = entry.get("status")
            title = entry.get("title", "")
            reference = entry.get("reference", "")
            checkout_observation = entry.get("checkout_observation", "")
            planned_date = entry.get("planned_date")
            
            # Parse title to extract tipo, pedido, and seller
            parts = title.split("-")
            tipo = parts[0] if len(parts) > 2 else None
            seller = parts[1] if len(parts) > 2 else None
            pedido = parts[-1] if len(parts) > 2 else None

            tracking_entry = SRTrackingData(
                tracking_id=tracking_id,
                rawJson=entry,
                status=status,
                title=title,
                tipo=tipo,
                pedido=pedido,
                seller=seller,
                reference=reference,
                checkout_observation=checkout_observation,
                planned_date=planned_date
            )
            tracking_entries.append(tracking_entry)

        except IntegrityError as e:
            messages.error(request, f"Integrity error saving tracking data for {tracking_id}: {e}")
        except Exception as e:
            messages.error(request, f"Unexpected error parsing or saving data for {tracking_id}: {e}")

    # Bulk save all tracking data for the date in one go
    SRTrackingData.objects.bulk_create(tracking_entries, ignore_conflicts=True)
    messages.info(request, f"Bulk saved tracking data for {len(tracking_entries)} entries")

def process_tracking_data(request, update_mode=False):
    """
    Process tracking data by fetching from the earliest or latest date 
    based on update_mode.

    Parameters:
    ----------
    update_mode : bool
        If True, fetches data starting from the latest planned_date in SRTrackingData (for updates).
        If False, fetches data starting from the earliest Order.fechaCreacion (for initial population).
    """
    start_date, end_date = None, None

    if update_mode:
        try:
            start_date = SRTrackingData.objects.latest("planned_date").planned_date + timezone.timedelta(days=1)
        except SRTrackingData.DoesNotExist:
            messages.error(request, "NO hay data en la base de OMS, sin rangos para actualizar.")
            return
    else:
        try:
            start_date = Order.objects.earliest("fechaCreacion").fechaCreacion.date()
        except Order.DoesNotExist:
            messages.error(request, "NO hay data en la base de OMS, sin rangos para poblar.")
            return

    try:
        end_date = Order.objects.latest("fechaCreacion").fechaCreacion.date()
    except Order.DoesNotExist:
        messages.error(request, "NO hay data en la base de OMS, sin fecha limite.")
        return
    
    # Ensure dates were found before proceeding
    if not start_date or not end_date:
        logger.info(request, "NO hay data en la base de OMS, sin rangos para actualizar.")
        return

    dates_to_process = [start_date + timezone.timedelta(days=i) for i in range((end_date - start_date).days + 1)]

    with ThreadPoolExecutor(max_workers=7) as executor:
        futures = {executor.submit(fetch_data_for_date, request, date): date for date in dates_to_process}
        
        for future in as_completed(futures):
            planned_date = futures[future]
            try:
                data = future.result()
                if data:
                    parse_and_save_data(request, data)
            except Exception as e:
                messages.error(request, f"Failed to process data for {planned_date}: {e}")
    
    logger.info("Batch processing complete.")


