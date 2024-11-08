import pandas as pd
from django.db.models import Prefetch
from .models import Order
from typing import List, Optional

import pandas as pd
from typing import List, Optional
from .models import Order

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

