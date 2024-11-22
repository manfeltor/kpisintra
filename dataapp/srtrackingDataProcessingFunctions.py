import pandas as pd
from django.db.models import Count
from dataapp.models import SRTrackingData, sr_checkout_observations_matrix
from datetime import datetime, timedelta
from django.utils.timezone import now
from usersapp.models import CustomUser

def get_sr_tracking_summary(request, sellers_objects=None):
    """
    Query the SRTrackingData model to summarize the number of trackings grouped by
    planned_date, checkout_observation, and seller. Limit to the last 12 months and return
    the result as a pandas DataFrame.
    
    Parameters:
    -----------
    request : HttpRequest
        The Django request object to access user details.
    seller : str, optional
        The seller name to filter data. Defaults to None.

    Returns:
    --------
    pd.DataFrame
        DataFrame with columns: planned_date, checkout_observation, seller, tracking_count
    """
    # Calculate the cutoff date for 12 months ago
    cutoff_date = now().date().replace(day=1) - timedelta(days=395)
    # cutoff_date = now().date().replace(day=1)

    # ORM query, filtered for the last 12 months
    user_role = request.user.role

    # if user_role == CustomUser.CLIENT:
    query = SRTrackingData.objects.filter(planned_date__gte=cutoff_date)
    query = query.filter(tipo="DIST")

    if user_role == CustomUser.CLIENT:
        seller = request.user.company
        query = query.filter(seller=seller)
    elif sellers_objects:
        sellers = [seller.name for seller in sellers_objects] if sellers_objects else None
        query = query.filter(seller__in=sellers)
        
    query = query.values(
            'planned_date', 'checkout_observation', 'seller'
        ).annotate(
            tracking_count=Count('tracking_id')
        ).order_by('planned_date', 'checkout_observation', 'seller')
        
    # Convert QuerySet to DataFrame
    df = pd.DataFrame.from_records(query)

    print(df)
    
    return df


def enrich_sr_tracking_summary(df):
    """
    Enrich the SR tracking summary DataFrame with 'label' and 'responsibility' columns 
    by matching 'checkout_observation' with 'id' in sr_checkout_observations_matrix.

    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame returned from get_sr_tracking_summary, with columns:
        ['planned_date', 'checkout_observation', 'tracking_count']

    Returns:
    --------
    pd.DataFrame
        The enriched DataFrame with added 'label' and 'responsibility' columns.
    """
    # Convert the sr_checkout_observations_matrix into a dict for faster lookups
    observations_dict = {
    key: {
        "label": value["label"],
        "responsibility": value.get("responsibility"),
        "type": value.get("type")
    }
    for key, value in sr_checkout_observations_matrix.items()
}

    # Add 'label' and 'responsibility' to the DataFrame
    df["label"] = df["checkout_observation"].map(lambda obs: observations_dict.get(obs, {}).get("label"))
    df["responsibility"] = df["checkout_observation"].map(lambda obs: observations_dict.get(obs, {}).get("responsibility"))
    df["type"] = df["checkout_observation"].map(lambda obs: observations_dict.get(obs, {}).get("type"))
    return df

def get_monthly_tracking_percentages(df):
    """
    Process the DataFrame to compute monthly percentages of 'failed' vs 'completed' trackings.

    Parameters:
    -----------
    df : pd.DataFrame
        Enriched DataFrame containing 'planned_date', 'checkout_observation', 'tracking_count',
        'label', and 'responsibility'.

    Returns:
    --------
    pd.DataFrame
        DataFrame with columns: 'month', 'type', 'percentage'.
    """
    # Convert planned_date to datetime (if not already)
    df['planned_date'] = pd.to_datetime(df['planned_date'])

    # Filter for the last 12 months
    one_year_ago = datetime.now() - timedelta(days=365)
    df = df[df['planned_date'] >= one_year_ago]

    # Extract month and year
    df['month'] = df['planned_date'].dt.to_period('M')

    # Group by month and type ('failed'/'completed')
    monthly_summary = (
        df.groupby(['month', 'type', 'seller', 'responsibility'])
        .agg(total_count=('tracking_count', 'sum'))
        .reset_index()
    )

    # Compute total trackings per month
    monthly_totals = monthly_summary.groupby('month')['total_count'].transform('sum')

    # Add percentage column
    monthly_summary['percentage'] = (monthly_summary['total_count'] / monthly_totals) * 100

    # Convert month back to a proper format for plotting
    monthly_summary['month'] = monthly_summary['month'].dt.to_timestamp()

    return monthly_summary