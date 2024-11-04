import time
import requests
from decouple import config

def fetch_sr_tracking_data_from_api(batch):
    base_url = config('SR_VISITS_BASE_URL')
    headers = {
        "authorization": config('SR_AUTH_TOKEN'),
        "content-type": "application/json"
    }

    # Dictionary to store results
    tracking_data = {}

    for trk in batch:
        url = f"{base_url}?tracking_id={trk}"
        success = False
        retries = 0

        while not success and retries < 3:
            try:
                response = requests.get(url, headers=headers)
                print(response.status_code, 'for', trk)
                
                if response.status_code == 200:
                    data = response.json()  # Directly store JSON response
                    tracking_data[trk] = data
                    success = True
                    time.sleep(0.1)  # Success delay

                else:
                    retries += 1
                    print(f"Attempt {retries} for tracking_id {trk} failed with status code {response.status_code}")
                    time.sleep(0.5)  # Failure delay

            except requests.exceptions.RequestException as e:
                retries += 1
                print(f"Request error for tracking_id {trk} on attempt {retries}: {e}")
                time.sleep(0.5)  # Failure delay

        if not success:
            # After 3 attempts, give up and set to None
            tracking_data[trk] = None
            print(f"Failed to fetch data for tracking_id {trk} after {retries} retries.")

    return tracking_data