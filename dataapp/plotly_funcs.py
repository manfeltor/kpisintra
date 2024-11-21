import plotly.graph_objects as go
import pandas as pd
from .main_functions import calculate_relation

def fallidos_vs_completados_graph(df, start_date, end_date, sellers=None):
    """
    Generate an interactive stacked bar graph for "Fallidos vs Completados" percentages using Plotly.

    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame containing 'month', 'type', 'seller', 'percentage'.
    start_date : datetime
        Start date for filtering.
    end_date : datetime
        End date for filtering.
    seller : list, optional
        Seller name to filter by. Defaults to None (include all sellers).

    Returns:
    --------
    str
        Plotly HTML div as a string to embed in the template.
    """

    print(sellers)

    start_date = pd.to_datetime(start_date)
    start_date = start_date.replace(tzinfo=None)
    end_date = pd.to_datetime(end_date)
    end_date = end_date.replace(tzinfo=None)
    # Filter the DataFrame based on the date range and seller
    filtered_df = df[
        (df['month'] >= (start_date)) &
        (df['month'] <= (end_date))
    ]
    if sellers:
        # filtered_df = filtered_df[filtered_df['seller'] == sellers]
        filtered_df = filtered_df[filtered_df['seller'].isin(sellers)]

    filtered_df['month'] = filtered_df['month'].dt.strftime('%Y-%m-%d')


    filtered_df = (
    filtered_df.groupby(['month', 'type'])
    .agg({'percentage': 'sum'})  # Aggregate percentages across all sellers if no specific seller
    .reset_index()
    )

    # Pivot the data for plotting
    pivot_table = filtered_df.pivot(index='month', columns='type', values='percentage').fillna(0)

    # Create traces for each type
    fig = go.Figure()
    for col in pivot_table.columns:
        fig.add_trace(go.Bar(
            x=pivot_table.index,
            y=pivot_table[col],
            name=col,
            hoverinfo="x+y+name"
        ))

    # Update layout for better visualization
    fig.update_layout(
        barmode='stack',
        title="Fallidos vs Completados - Últimos 12 Meses",
        xaxis=dict(
        title="Mes",
        type="category",  # Force x-axis to be categorical
        tickformat='%b %Y'
        ),
        yaxis_title="Porcentaje (%)",
        legend_title="Tipo",
        template="plotly_white",
        margin=dict(l=40, r=40, t=40, b=40),
        hovermode="x unified"
    )

    # Return the Plotly div
    return fig.to_html(full_html=False)


def failed_responsibility_breakdown_graph(df, start_date, end_date, sellers=None):
    """
    Generate a bar chart to show failed tracking reasons broken down by responsibility.

    Parameters:
    -----------
    df : pd.DataFrame
        The relativized DataFrame from the previous graph.
    start_date : datetime
        Start date for filtering.
    end_date : datetime
        End date for filtering.
    seller : str, optional
        If provided, filters the data for a specific seller.

    Returns:
    --------
    str
        The HTML representation of the Plotly graph.
    """
    start_date = pd.to_datetime(start_date)
    start_date = start_date.replace(tzinfo=None)
    end_date = pd.to_datetime(end_date)
    end_date = end_date.replace(tzinfo=None)

    # Filter for the specified date range
    filtered_df = df[
        (df['month'] >= start_date) & 
        (df['month'] <= end_date)
    ]

    # If a seller is specified, filter for that seller
    if sellers:
        # filtered_df = filtered_df[filtered_df['seller'] == sellers]
        filtered_df = filtered_df[filtered_df['seller'].isin(sellers)]


    filtered_df['month'] = filtered_df['month'].dt.strftime('%Y-%m-%d')

    filtered_df1 = (
    filtered_df.groupby(['month', 'type', 'responsibility'], as_index=False)
    .agg({'percentage': 'sum'})
    )

    filtered_df2 = filtered_df1[filtered_df1['type'] == 'failed']

    pivot_table = filtered_df2.pivot(index='month', columns='responsibility', values='percentage').fillna(0)

    fig = go.Figure()
    for col in pivot_table.columns:
        fig.add_trace(go.Bar(
            x=pivot_table.index,
            y=pivot_table[col],
            name=col,
            hoverinfo="x+y+name"
        ))

    # Update layout for better visualization
    fig.update_layout(
        barmode='stack',
        title="Desambiguacion concepto fallidos",
        xaxis_title="Mes",
        yaxis_title="Porcentaje relativo (%)",
        legend_title="Tipo",
        template="plotly_white",
        xaxis=dict(tickformat='%b %Y'),
        margin=dict(l=40, r=40, t=40, b=40),
        hovermode="x unified"
    )

    return fig.to_html(full_html=False)