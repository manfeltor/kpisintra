import plotly.graph_objects as go
import pandas as pd

def fallidos_vs_completados_graph(df, start_date, end_date, seller=None):
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
    seller : str, optional
        Seller name to filter by. Defaults to None (include all sellers).

    Returns:
    --------
    str
        Plotly HTML div as a string to embed in the template.
    """

    start_date = pd.to_datetime(start_date)
    start_date = start_date.replace(tzinfo=None)
    end_date = pd.to_datetime(end_date)
    end_date = end_date.replace(tzinfo=None)
    # Filter the DataFrame based on the date range and seller
    filtered_df = df[
        (df['month'] >= (start_date)) &
        (df['month'] <= (end_date))
    ]
    if seller:
        filtered_df = filtered_df[filtered_df['seller'] == seller]


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
        xaxis_title="Mes",
        yaxis_title="Porcentaje (%)",
        legend_title="Tipo",
        template="plotly_white",
        xaxis=dict(tickformat='%b %Y'),
        margin=dict(l=40, r=40, t=40, b=40),
        hovermode="x unified"
    )

    # Return the Plotly div
    return fig.to_html(full_html=False)