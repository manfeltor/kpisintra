import pandas as pd
from .models import Order
from usersapp.models import CustomUser
from .main_functions import calculate_busy_days

def query_primary_order_df_interior(request, sellers_objects, start_date, end_date, fields=None):
    """
    Query the primary order data based on user role and seller filters, dynamically fetching fields.

    Parameters:
    -----------
    request : HttpRequest
        The Django request object to access user details.
    sellers_objects : QuerySet or list
        The sellers to filter by.
    fields : list, optional
        List of fields to include in the query. Defaults to None, which fetches all fields.

    Returns:
    --------
    pd.DataFrame
        DataFrame containing the queried order data.
    """
    tipos = ["DIST", "SUCA"]
    query = Order.objects.filter(tipo__in=tipos)
    query = query.filter(zona="INTERIOR")
    query = query.filter(trackingTransporte__isnull=False)
    query = query.filter(fechaDespacho__isnull=False)
    query = query.filter(fechaEntrega__isnull=False)
    query = query.filter(fechaDespacho__gte=start_date, fechaDespacho__lte=end_date)

    user_role = request.user.role

    if user_role == CustomUser.CLIENT:
        seller = request.user.company
        query = query.filter(seller=seller)
    elif sellers_objects:
        sellers = [seller.name for seller in sellers_objects] if sellers_objects else None
        query = query.filter(seller__in=sellers)

    # Use the provided fields or default to fetching all fields
    if fields is None:
        fields = [
            "pedido",  # Example: Replace with actual field names
            "flujo",
            "seller",
            "sucursal",
            "estadoPedido",
            "fechaCreacion",
            "fechaRecepcion",
            "tipo",
            "fechaDespacho",
            "fechaEntrega",
            "lpn",
            "estadoLpn",
            "provincia",
            "localidad",
            "zona",
            "trackingDistribucion",
            "trackingTransporte",
            "codigoPostaltxt",
            "codigoPostal",
            "order_data",
        ]

    query = query.values(*fields)

    # Convert to DataFrame
    df = pd.DataFrame.from_records(query)

    return df


def enrich_primary_df_timedeltas(primary_df, start_col, end_col):
    """
    Adds raw and busy delta days to the primary DataFrame.

    Parameters:
    -----------
    primary_df : pd.DataFrame
        The main DataFrame containing the date columns.
    start_col : str
        Column name representing the start date.
    end_col : str
        Column name representing the end date.

    Returns:
    --------
    pd.DataFrame
        The enriched DataFrame with 'raw_delta_days' and 'busy_delta_days'.
    """
    # Ensure datetime conversion
    primary_df[start_col] = pd.to_datetime(primary_df[start_col], errors='coerce')
    primary_df[end_col] = pd.to_datetime(primary_df[end_col], errors='coerce')

    # Filter rows where both dates are present
    primary_df = primary_df.dropna(subset=[start_col, end_col])

    # Calculate raw delta days
    primary_df['raw_delta_days'] = (primary_df[end_col] - primary_df[start_col]).dt.days

    # Calculate busy delta days
    primary_df['busy_delta_days'] = primary_df.apply(
        lambda row: calculate_busy_days(row[start_col], row[end_col]), axis=1
    )

    return primary_df


def calculate_weighted_averages_with_hierarchy(enriched_df, heriarchy_col, child_col, first_col, second_col):
    """
    Calculate weighted averages while preserving hierarchy and child relationships.

    Parameters:
    -----------
    enriched_df : pd.DataFrame
        The enriched DataFrame containing data.
    heriarchy_col : str
        Column representing the hierarchy level (e.g., "codigoPostal__partido").
    child_col : str
        Column representing the child level (e.g., "codigoPostal__localidad").
    first_col : str
        Column representing the first metric to calculate weighted averages for (e.g., "raw_delta_days").
    second_col : str
        Column representing the second metric to calculate weighted averages for (e.g., "busy_delta_days").

    Returns:
    --------
    pd.DataFrame
        DataFrame containing weighted averages for each group, preserving hierarchy and child relationships.
    """

    # Step 1: Group by heriarchy_col and child_col to calculate counts and averages
    grouped_df = enriched_df.groupby([heriarchy_col, child_col]).agg(
        first_values_count=(first_col, 'count'),
        first_values_avg=(first_col, 'mean'),
        second_values_count=(second_col, 'count'),
        second_values_avg=(second_col, 'mean')
    ).reset_index()

    # Step 2: Calculate weighted averages for the child level (localidad) grouped by the hierarchy level (partido)
    grouped_df['first_weighted_avg'] = grouped_df['first_values_avg'] * grouped_df['first_values_count'] / grouped_df.groupby(heriarchy_col)['first_values_count'].transform('sum')
    grouped_df['second_weighted_avg'] = grouped_df['second_values_avg'] * grouped_df['second_values_count'] / grouped_df.groupby(heriarchy_col)['second_values_count'].transform('sum')

    # Ensure output contains the required columns for `create_filtered_chart`
    result_df = grouped_df[[heriarchy_col, child_col, 'first_weighted_avg', 'second_weighted_avg']].copy()

    # Rename columns to fit the `y_col` input for `create_filtered_chart`
    result_df.rename(columns={
        'first_weighted_avg': f'{first_col}_weighted',
        'second_weighted_avg': f'{second_col}_weighted'
    }, inplace=True)

    return result_df


def calculate_weighted_averages_higher_level(enriched_df, group_col, first_col, second_col):
    """
    Calculate weighted averages for the highest hierarchy level.

    Parameters:
    -----------
    enriched_df : pd.DataFrame
        The enriched DataFrame containing data.
    group_col : str
        Column representing the grouping level (e.g., "codigoPostal__provincia").
    first_col : str
        Column representing the first metric to calculate weighted averages for (e.g., "raw_delta_days").
    second_col : str
        Column representing the second metric to calculate weighted averages for (e.g., "busy_delta_days").

    Returns:
    --------
    pd.DataFrame
        DataFrame containing weighted averages for the highest hierarchy level.
    """
    grouped_df = enriched_df.groupby(group_col).agg(
        first_values_count=(first_col, 'count'),
        first_values_avg=(first_col, 'mean'),
        second_values_count=(second_col, 'count'),
        second_values_avg=(second_col, 'mean')
    ).reset_index()

    grouped_df['first_weighted_avg'] = grouped_df['first_values_avg'] * grouped_df['first_values_count'] / grouped_df['first_values_count'].sum()
    grouped_df['second_weighted_avg'] = grouped_df['second_values_avg'] * grouped_df['second_values_count'] / grouped_df['second_values_count'].sum()

    return grouped_df[[group_col, 'first_weighted_avg', 'second_weighted_avg']].rename(
        columns={
            'first_weighted_avg': f'{first_col}_weighted',
            'second_weighted_avg': f'{second_col}_weighted'
        }
    )


def generate_frequency_df(enriched_df):
    """
    Generates frequency distribution dataframes for raw_delta_days and busy_delta_days.
    
    Parameters:
    enriched_df (pd.DataFrame): The dataframe containing the columns 'raw_delta_days' and 'busy_delta_days'
    
    Returns:
    dict: A dictionary with two dataframes: one for raw and one for busy
    """
    
    # Initialize dictionaries to hold the frequency data
    frequency_data = {
        'raw': [],
        'busy': []
    }

    # Get the maximum values for raw and busy delta days across all provinces
    max_raw_delta = enriched_df['raw_delta_days'].max()
    max_busy_delta = enriched_df['busy_delta_days'].max()

    # Group by province (codigoPostal__provincia)
    grouped_by_province = enriched_df.groupby('codigoPostal__provincia')

    for province, group in grouped_by_province:
        # Calculate frequency distribution for raw_delta_days
        raw_freq = group['raw_delta_days'].value_counts().sort_index()
        
        # Ensure the range from 0 to max_raw_delta is covered, even if there are missing values
        raw_freq_full = raw_freq.reindex(range(0, max_raw_delta + 1), fill_value=0)
        
        # Append the result for raw_delta_days to the dictionary
        for delta_day, frequency in raw_freq_full.items():
            frequency_data['raw'].append({
                'codigoPostal__provincia': province,
                'raw_delta_days': delta_day,
                'frequency': frequency
            })

        # Calculate frequency distribution for busy_delta_days
        busy_freq = group['busy_delta_days'].value_counts().sort_index()
        
        # Ensure the range from 0 to max_busy_delta is covered, even if there are missing values
        busy_freq_full = busy_freq.reindex(range(0, max_busy_delta + 1), fill_value=0)
        
        # Append the result for busy_delta_days to the dictionary
        for delta_day, frequency in busy_freq_full.items():
            frequency_data['busy'].append({
                'codigoPostal__provincia': province,
                'busy_delta_days': delta_day,
                'frequency': frequency
            })

    # Convert the frequency data into separate DataFrames
    raw_df = pd.DataFrame(frequency_data['raw'])
    busy_df = pd.DataFrame(frequency_data['busy'])

    return raw_df, busy_df