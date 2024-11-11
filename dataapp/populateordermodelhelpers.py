import pandas as pd
from django.utils import timezone
from tkinter import Tk, filedialog

# POPULATE ORDER MODEL Helper function to safely parse a date from the Excel file
def parse_date(date_value):
    if pd.isna(date_value):
        return None
    try:
        parsed_date = pd.to_datetime(date_value)

        if parsed_date.tzinfo is None:
            return timezone.make_aware(parsed_date)
        return parsed_date
    except ValueError:
        return None

# POPULATE ORDER MODEL Function to select folder path
def select_folder():
    root = Tk()
    root.withdraw()
    folder_path = filedialog.askdirectory()
    root.destroy()
    return folder_path