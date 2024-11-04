import time
import requests
from decouple import config
from concurrent.futures import ThreadPoolExecutor, as_completed

def fetch_single_tracking_data(trk):
    base_url = config('SR_VISITS_BASE_URL')
    headers = {
        "authorization": config('SR_AUTH_TOKEN'),
        "content-type": "application/json"
    }
    
    url = f"{base_url}?tracking_id={trk}"
    retries = 0
    
    while retries < 3:
        try:
            response = requests.get(url, headers=headers)
            print(response.status_code, 'for', trk)
            
            if response.status_code == 200:
                return trk, response.json()  # Return tracking ID and data
            else:
                retries += 1
                print(f"Attempt {retries} for tracking_id {trk} failed with status code {response.status_code}")
                time.sleep(0.5)  # Failure delay

        except requests.exceptions.RequestException as e:
            retries += 1
            print(f"Request error for tracking_id {trk} on attempt {retries}: {e}")
            time.sleep(0.5)  # Failure delay
    
    # Return None if all attempts fail
    print(f"Failed to fetch data for tracking_id {trk} after {retries} retries.")
    return trk, None

def fetch_sr_tracking_data_from_api(batch, max_workers=5):
    tracking_data = {}
    
    # Using ThreadPoolExecutor to parallelize requests
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(fetch_single_tracking_data, trk): trk for trk in batch}
        
        for future in as_completed(futures):
            trk, data = future.result()
            tracking_data[trk] = data  # Store the result in tracking_data dictionary
    
    return tracking_data