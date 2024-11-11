import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from django.db import IntegrityError
from django.utils import timezone
from dataapp.models import SRTrackingData, Order
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_data_for_date(planned_date):
    url = f"https://api.simpliroute.com/v1/routes/visits/?planned_date={planned_date}"
    headers = {
        "authorization": "Token abc123",
        "content-type": "application/json"
    }
    
    for attempt in range(3):  # Retry up to 3 times
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                return data  # Return data if successful
            else:
                logger.error(f"Failed to fetch data for {planned_date}: {response.status_code}")
        except requests.RequestException as e:
            logger.error(f"Error on attempt {attempt+1} for date {planned_date}: {e}")
        time.sleep(0.2)  # Sleep before retrying
    return None  # Return None if all retries fail

def parse_and_save_data(data):
    for entry in data:
        try:
            # Extract fields from JSON response
            raw_json = entry
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

            # Save to SRTrackingData
            tracking_data = SRTrackingData(
                tracking_id=tracking_id,
                rawJson=raw_json,
                status=status,
                title=title,
                tipo=tipo,
                pedido=pedido,
                seller=seller,
                reference=reference,
                checkout_observation=checkout_observation,
                planned_date=planned_date
            )
            tracking_data.save()
            logger.info(f"Saved tracking data for {tracking_id}")
        
        except IntegrityError as e:
            logger.error(f"Integrity error saving tracking data for {tracking_id}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error parsing or saving data: {e}")

def process_tracking_data():
    # Retrieve min and max dates
    min_date = Order.objects.earliest("fechaCreacion").fechaCreacion.date()
    max_date = Order.objects.latest("fechaCreacion").fechaCreacion.date()
    
    date_range = (max_date - min_date).days
    dates_to_process = [min_date + timezone.timedelta(days=i) for i in range(date_range + 1)]
    
    with ThreadPoolExecutor(max_workers=7) as executor:
        futures = {}
        for date in dates_to_process:
            # Check if data already exists for this date
            if SRTrackingData.objects.filter(planned_date=date).exists():
                logger.info(f"Data already exists for {date}. Skipping.")
                continue
            
            # Schedule API fetch for date
            futures[executor.submit(fetch_data_for_date, date)] = date

        # Process completed futures
        for future in as_completed(futures):
            planned_date = futures[future]
            try:
                data = future.result()
                if data:
                    parse_and_save_data(data)
            except Exception as e:
                logger.error(f"Failed to process data for {planned_date}: {e}")
    
    logger.info("Batch processing complete.")