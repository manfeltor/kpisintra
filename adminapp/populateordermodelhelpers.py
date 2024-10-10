import pandas as pd
from django.utils import timezone
from tkinter import Tk, filedialog

# POPULATE ORDER MODEL Helper function to safely parse a date from the Excel file
def parse_date(date_value):
    if pd.isna(date_value):
        return None
    try:
        # Convert to a pandas datetime object
        parsed_date = pd.to_datetime(date_value)

        # Check if the date is naive (doesn't have timezone info)
        if parsed_date.tzinfo is None:
            # Make it timezone-aware using Django's timezone settings
            return timezone.make_aware(parsed_date)
        return parsed_date
    except ValueError:
        return None

# POPULATE ORDER MODEL Function to select folder path
def select_folder():
    root = Tk()
    root.withdraw()  # Hide the Tkinter root window
    folder_path = filedialog.askdirectory()  # Open a dialog to select folder
    root.destroy()  # Close Tkinter
    return folder_path