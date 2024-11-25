import pandas as pd
from .models import Order
from usersapp.models import CustomUser

def query_primary_order_df(request, sellers_objects, fields=None):
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