import pandas as pd
from django.db.models import Count
from dataapp.models import SRTrackingData, sr_checkout_observations_matrix
from datetime import datetime, timedelta
from django.utils.timezone import now
from usersapp.models import CustomUser

def get_sr_tracking_summary(request, sellers_objects=None, failed=False, start_date=None, end_date=None):
    """
    Query the SRTrackingData model to summarize trackings grouped by date, observation, and seller.

    Parameters:
    -----------
    request : HttpRequest
        The Django request object to access user details.
    sellers_objects : list or QuerySet, optional
        Sellers to filter by.
    failed : bool, optional
        Whether to filter for failed statuses. Defaults to False.
    start_date : str or None, optional
        Start date for filtering. Defaults to None.
    end_date : str or None, optional
        End date for filtering. Defaults to None.

    Returns:
    --------
    pd.DataFrame
        DataFrame with columns: planned_date, checkout_observation, seller, tracking_count.
    """
    cutoff_date = now().date().replace(day=1) - timedelta(days=395)

    # print(type(start_date))
    
    if start_date == None:
        query = SRTrackingData.objects.filter(planned_date__gte=cutoff_date)
    else:
        query = SRTrackingData.objects.filter(planned_date__gte=start_date)

    if end_date:
        query = query.filter(planned_date__lte=end_date)

    query = query.filter(tipo="DIST")
    query = query.exclude(checkout_observation="9e4619d2-240f-4efb-bc73-f91e9469cd91")
    query = query.exclude(checkout_observation="1a10310b-e710-4d66-8153-44ca9a88a8dc")


    if failed:
        query = query.filter(status='failed')

    user_role = request.user.role
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

    df = pd.DataFrame.from_records(query)

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

def get_monthly_tracking_percentages(df, column):
    """
    Process the DataFrame to compute monthly percentages of 'failed' vs 'completed' trackings.

    Parameters:
    -----------
    df : pd.DataFrame
        Enriched DataFrame containing 'planned_date', 'checkout_observation', 'tracking_count',
        'label', and 'responsibility'.

    column: str
        Argument for grouping the data percentages

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
        df.groupby(['month', 'type', 'seller', column])
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