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
    print(query)
    query = query.filter(zona="INTERIOR")
    query = query.filter(trackingTransporte__isnull=False)
    query = query.filter(fechaDespacho__isnull=False)
    query = query.filter(fechaEntrega__isnull=False)
    query = query.filter(fechaDespacho__gte=start_date, fechaDespacho__lte=end_date)
    print(query)
    

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