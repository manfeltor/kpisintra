import pandas as pd
from .models import Order, Company
from typing import List, Optional
from .forms import FilterForm
from django.utils.timezone import now
from datetime import datetime, timedelta
from numpy import busday_count


def get_orders_dataframe(
    fields: Optional[List[str]] = None,
    unique_orders: bool = False,
    SRdeserialization: Optional[List[str]] = None,
    CAdeserialization: Optional[List[str]] = None,
    postalCodeData: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Generates a DataFrame from the Order model with optional deserialization and customization.

    Parameters
    ----------
    fields : list of str, optional
        List of field names from the Order model to include in the DataFrame. 
        If None, all fields are included.
    
    unique_orders : bool, default False
        If True, eliminates duplicate entries based on the 'pedido' field to include only unique orders.
    
    SRdeserialization : list of str, optional
        List of keys from the SRTrackingData.rawJson field to include as separate columns.
        If None, SRTrackingData is included as a single rawJson object.
    
    CAdeserialization : list of str, optional
        List of keys from the CATrackingData.rawJson field to include as separate columns.
        If None, CATrackingData is included as a single rawJson object.
    
    postalCodeData : list of str, optional
        List of field names from the PostalCodes model to include in the DataFrame.
        If None, only 'cp' (the postal code) is included.

    Returns
    -------
    pd.DataFrame
        DataFrame containing the specified fields and deserialized JSON data as columns.
    """
    
    # Set base queryset and prepare fields for selection
    order_fields = fields or [f.name for f in Order._meta.fields]
    order_qs = Order.objects.all()
    
    # Add related fields as necessary for deserialization
    if SRdeserialization:
        order_fields.append('trackingDistribucion__rawJson')
    if CAdeserialization:
        order_fields.append('trackingTransporte__rawJson')
    if postalCodeData:
        postal_columns = [f"codigoPostal__{field}" for field in postalCodeData]
        order_fields.extend(postal_columns)
    else:
        # order_fields.append("codigoPostal__cp")
        pass
    
    # Retrieve the selected fields from the queryset
    order_qs = order_qs.values(*order_fields)
    df = pd.DataFrame.from_records(order_qs)
    
    # Handle unique orders
    if unique_orders:
        df = df.drop_duplicates(subset=['pedido'])
    
        # Deserialize SRTrackingData fields if specified
    if SRdeserialization:
        if 'trackingDistribucion__rawJson' in df.columns:
            # Only apply deserialization where rawJson is not None
            df = pd.concat([
                df.drop(columns=['trackingDistribucion__rawJson']),
                df['trackingDistribucion__rawJson'].apply(lambda x: pd.Series(x) if x is not None else pd.Series([None] * len(SRdeserialization), index=SRdeserialization))])

    # Deserialize CATrackingData fields if specified
    if CAdeserialization:
        if 'trackingTransporte__rawJson' in df.columns:
            # Only apply deserialization where rawJson is not None
            df = pd.concat([
                df.drop(columns=['trackingTransporte__rawJson']),
                df['trackingTransporte__rawJson'].apply(lambda x: pd.Series(x) if x is not None else pd.Series([None] * len(CAdeserialization), index=CAdeserialization))], axis=1)

    # Rename PostalCodes column(s)
    if postalCodeData:
        df.rename(columns={f"codigoPostal__{field}": field for field in postalCodeData}, inplace=True)
    else:
        df.rename(columns={"codigoPostal__cp": "postal_code"}, inplace=True)
    
    return df


def calculate_relation(df, A, C):
    """
    Calculate the sum of 'C' for each 'A' value and compute the relation for each row.

    Parameters:
    ----------
    df : pd.DataFrame
        DataFrame containing columns 'A', 'B', and 'C'.    
    
    A : str
        Name of the category column to make calculations

    C : str
        Name of the column with the values for each category

    Returns:
    --------
    pd.DataFrame
        DataFrame with additional columns 'Sum' and 'relation'.
    """
    # Calculate the sum of 'C' for each 'A' value
    sum_df = df.groupby(A)[C].sum().reset_index().rename(columns={C: 'Sum'})
    
    # Merge the sum back into the original DataFrame
    df = df.merge(sum_df, on=A)
    
    # Calculate the relation for each row
    df['relation'] = df[C] / df['Sum']
    
    return df


def define_dates_and_sellers(req, form):

    cutoff_date = now().date().replace(day=1) - timedelta(days=395)

    if form.is_valid():
        start_date = form.cleaned_data.get('start_date') or cutoff_date
        end_date = form.cleaned_data.get('end_date') or now()
        sellers = form.cleaned_data.get('sellers') or None

    else:
        start_date = cutoff_date
        end_date = now()
        sellers = None

    if start_date < cutoff_date:
        start_date = cutoff_date

    # Ensure start_date and end_date are `datetime.date` objects
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

    return start_date, end_date, sellers


def calculate_busy_days(start, end):
    return busday_count(start.date(), end.date())


def strip_last_n_percent(df, value_col, frequency_col, strip_percentage):
    """
    Strips a specified percentage of the total frequency from the given DataFrame, 
    starting from the highest values of the `value_col` and adjusting the frequencies
    in the `frequency_col`. This is useful when you want to remove the "top" frequency 
    counts in a frequency distribution.

    Parameters:
    - df (pandas.DataFrame): The input DataFrame containing the frequency data.
    - value_col (str): The column name representing the values (e.g., 'n', 'days').
    - frequency_col (str): The column name representing the frequencies to be stripped.
    - strip_percentage (float): The percentage of the total frequency to remove (e.g., 0.11 for 11%).

    Returns:
    - pandas.DataFrame: The modified DataFrame with the frequencies adjusted.

    Procedure:
    1. Calculates the total sum of the frequencies in the `frequency_col`.
    2. Determines how much frequency (in the form of a value) to strip based on the `strip_percentage`.
    3. Iterates through the DataFrame starting from the highest values in `value_col` (sorted in descending order).
    4. Reduces the frequencies from the rows with the largest `value_col` until the total stripped amount is reached.
       - If the current frequency is greater than or equal to the remaining amount to strip, it is reduced accordingly.
       - If the frequency is smaller than the remaining amount to strip, it is set to 0, and the remaining strip amount is reduced by that frequency.
    5. Stops when the required amount has been stripped from the DataFrame.

    Example:
    >>> data = {'n': [20, 19, 18, 17, 16], 'frequency': [10, 60, 150, 200, 500]}
    >>> df = pd.DataFrame(data)
    >>> strip_last_n_percent(df, 'n', 'frequency', 0.11)

    This will strip 11% of the total frequencies, starting from the largest `n` values.
    """

    # Step 1: Calculate the total frequency
    total_frequency = df[frequency_col].sum()

    # Step 2: Calculate 11% of the total frequency
    percentage_to_strip = total_frequency * strip_percentage

    # Step 3: Iterate through the DataFrame from max 'n' down to 0 and subtract from frequencies
    remaining_to_strip = percentage_to_strip

    for index, row in df.sort_values(by=value_col, ascending=False).iterrows():
        if remaining_to_strip == 0:
            break

        # If current frequency is greater than or equal to the remaining amount to strip
        if row[frequency_col] >= remaining_to_strip:
            df.at[index, frequency_col] = row[frequency_col] - remaining_to_strip
            remaining_to_strip = 0
        else:
            # If the current frequency is less than the remaining to strip, set it to 0
            df.at[index, frequency_col] = 0
            remaining_to_strip -= row[frequency_col]
    
    return df


def add_cumulative_percentage(df, value_col, frequency_col):
    """
    Adds cumulative and cumulative percentage columns to a DataFrame.

    Parameters:
    - df (pandas.DataFrame): The input DataFrame with values and frequencies.
    - value_col (str): The column name representing the values (e.g., 'n', 'days').
    - frequency_col (str): The column name representing the frequencies.

    Returns:
    - pandas.DataFrame: The modified DataFrame with the cumulative and cumulative_percentage columns.
    """

    # Step 1: Sort the DataFrame by the value column in ascending order
    df_sorted = df.sort_values(by=value_col, ascending=True)

    # Step 2: Calculate the cumulative sum of the frequencies
    df_sorted['cumulative'] = df_sorted[frequency_col].cumsum()

    # Step 3: Calculate the cumulative percentage based on the total frequency
    total_frequency = df_sorted[frequency_col].sum()
    df_sorted['cumulative_percentage'] = (df_sorted['cumulative'] / total_frequency) * 100
    df_sorted['cumulative_percentage'].iloc[-2:] = df_sorted['cumulative_percentage'].iloc[-2:].astype(int)
    df_sorted['cumulative_percentage'] = df_sorted['cumulative_percentage'].replace(100, 99)

    return df_sorted


def add_relative_percentage(df, order_col):
    """
    Adds a column to the dataframe that represents the relative percentage of orders
    for each province based on the total number of orders.
    
    Parameters:
    - df (pandas.DataFrame): The dataframe containing the 'codigoPostal__provincia' and 'pedido' columns.
    - order_col (str): The column name representing the number of orders (e.g., 'pedido').
    
    Returns:
    - pandas.DataFrame: The dataframe with an additional 'relative_percentage' column.
    """
    # Calculate total orders
    total_orders = df[order_col].sum()

    # Add a new column for the relative percentage of orders for each province
    df['relative_percentage'] = (df[order_col] / total_orders) * 100
    df1 = df.sort_values(by='relative_percentage', ascending=True)
    
    return df1

def filter_df_date_range(df, date_col, start_date, end_date):
    """
    Filters a DataFrame to include rows where the date in `date_col` 
    is within the range specified by `start_date` and `end_date`.

    Parameters:
    - df (pd.DataFrame): The input DataFrame to filter.
    - date_col (str): The name of the column containing date values.
    - start_date (str or pd.Timestamp): The start of the date range (inclusive).
    - end_date (str or pd.Timestamp): The end of the date range (inclusive).

    Returns:
    - pd.DataFrame: A filtered DataFrame containing rows within the specified date range.
    """
    # Ensure the date column is in datetime format
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')

    # Filter the DataFrame based on the date range
    filtered_df = df[(df[date_col] >= pd.to_datetime(start_date)) & (df[date_col] <= pd.to_datetime(end_date))]

    return filtered_df