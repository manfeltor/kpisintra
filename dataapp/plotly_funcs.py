import plotly.graph_objects as go
import pandas as pd
from .main_functions import calculate_relation

def fallidos_vs_completados_graph(df, start_date, end_date, sellers_objects=None):
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


    start_date = pd.to_datetime(start_date)
    start_date = start_date.replace(tzinfo=None)
    end_date = pd.to_datetime(end_date)
    end_date = end_date.replace(tzinfo=None)
    # Filter the DataFrame based on the date range and seller
    filtered_df = df[
        (df['month'] >= (start_date)) &
        (df['month'] <= (end_date))
    ]

    sellers = [seller.name for seller in sellers_objects] if sellers_objects else None

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


def failed_responsibility_breakdown_graph(df, start_date, end_date, sellers_objects=None):
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

    sellers = [seller.name for seller in sellers_objects] if sellers_objects else None

    # If a seller is specified, filter for that seller
    if sellers:
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


def failed_responsibility_desambiguation_transport_vs_client(df, start_date, end_date, transport=False, sellers_objects=None):

    start_date = pd.to_datetime(start_date)
    start_date = start_date.replace(tzinfo=None)
    end_date = pd.to_datetime(end_date)
    end_date = end_date.replace(tzinfo=None)

    # Filter for the specified date range
    filtered_df = df[
        (df['month'] >= start_date) & 
        (df['month'] <= end_date)
    ]

    sellers = [seller.name for seller in sellers_objects] if sellers_objects else None

    # If a seller is specified, filter for that seller
    if sellers:
        filtered_df = filtered_df[filtered_df['seller'].isin(sellers)]

    if transport:
        responsibility_labels_matrix = ["fueraDeRutaAsignada", "mercaderiaNoDespachada", "noColectado", "demorasOperativas"]
    else:
        responsibility_labels_matrix = ["ausente", "domicilioIncorrecto", "cancelado", "zonaPeligrosa", "rechazado"]

    filtered_df['month'] = filtered_df['month'].dt.strftime('%Y-%m-%d')
    # filtered_df = filtered_df[filtered_df['responsibility'] == 'transporte']
    filtered_df = filtered_df[filtered_df['label'].isin(responsibility_labels_matrix)]

    filtered_df1 = (
    filtered_df.groupby(['month', 'type', 'label'], as_index=False)
    .agg({'percentage': 'sum'})
    )

    pivot_table = filtered_df1.pivot(index='month', columns='label', values='percentage').fillna(0)

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


def create_bar_chart(df, group_col, y_col, title):
    fig = go.Figure()
    
    # Create bar traces
    for y in y_col:
        fig.add_trace(go.Bar(
            x=df[group_col],
            y=df[y],
            name=y,
            hoverinfo="x+y+name"
        ))

    # Calculate stats for each metric
    stats_texts = ["stats:"]
    for y in y_col:
        avg = df[y].mean()
        cv = (df[y].std() / avg * 100) if avg else 0
        mode = df[y].mode().iloc[0] if not df[y].mode().empty else "N/A"
        stats_texts.append(f"{y}: Avg={round(avg, 2)}, CV={round(cv, 2)}%, Mode={mode}")
    
    # Combine stats into a single annotation text
    stats_text = "<br>".join(stats_texts)
    fig.add_annotation(
        text=stats_text,
        xref="paper", yref="paper",
        x=0.5, y=1.15,  # Positioning above the graph
        showarrow=False,
        font=dict(size=12),
        align="center"
    )
    
    # Update layout
    fig.update_layout(
        barmode='group',
        title=title,
        xaxis_title=group_col,
        yaxis_title="Days",
        legend_title="Metrics",
        template="plotly_white",
        height=600,  # Adjusted height
        margin=dict(t=100, b=100)  # Adjusted margins for annotations
    )

    return fig.to_html(full_html=False)


def create_filtered_chart(df, group_col, sub_group_col, y_col, title):
    partidos = df[group_col].unique()

    fig = go.Figure()

    # Create traces for each 'codigoPostal__localidad' grouped by the metrics
    for partido in partidos:
        for y in y_col:
            filtered_df = df[df[group_col] == partido]
            fig.add_trace(go.Bar(
                x=filtered_df[sub_group_col],
                y=filtered_df[y],
                name=f"{y} ({partido})",
                hoverinfo="x+y+name",
                visible=(partido == partidos[0])  # Show only the first partido by default
            ))

    # Calculate general stats for "All Partidos"
    general_avg_raw = df['raw_delta_days'].mean()
    general_cv_raw = df['raw_delta_days'].std() / general_avg_raw * 100 if general_avg_raw else 0
    general_mode_raw = df['raw_delta_days'].mode().iloc[0] if not df['raw_delta_days'].mode().empty else "N/A"

    general_avg_busy = df['busy_delta_days'].mean()
    general_cv_busy = df['busy_delta_days'].std() / general_avg_busy * 100 if general_avg_busy else 0
    general_mode_busy = df['busy_delta_days'].mode().iloc[0] if not df['busy_delta_days'].mode().empty else "N/A"

    # Create a default annotation for "All Partidos"
    annotation_text = (
        f"General Avg, CV & Mode:<br>"
        f"raw_delta_days: Avg={round(general_avg_raw, 2)}, CV={round(general_cv_raw, 2)}%, Mode={general_mode_raw}<br>"
        f"busy_delta_days: Avg={round(general_avg_busy, 2)}, CV={round(general_cv_busy, 2)}%, Mode={general_mode_busy}"
    )

    # Add a default annotation
    fig.add_annotation(
        text=annotation_text,
        xref="paper", yref="paper",
        x=0.5, y=1.15,  # Centered above the graph
        showarrow=False,
        font=dict(size=12),
        align="center"
    )

    # Dropdown buttons to toggle visibility and update annotations
    dropdown_buttons = [
        {
            'label': 'All Partidos',
            'method': 'update',
            'args': [
                {'visible': [True] * len(fig.data)},  # Show all traces
                {
                    'title.text': 'Averages by Localidad and Partido',
                    'annotations': [
                        {
                            'text': annotation_text,
                            'xref': "paper", 'yref': "paper",
                            'x': 0.5, 'y': 1.15,
                            'showarrow': False,
                            'font': {'size': 12},
                            'align': "center"
                        }
                    ]
                }
            ]
        }
    ]

    # Add dropdown options for each partido
    for partido in partidos:
        filtered_df = df[df[group_col] == partido]
        avg_raw = filtered_df['raw_delta_days'].mean()
        cv_raw = filtered_df['raw_delta_days'].std() / avg_raw * 100 if avg_raw else 0
        mode_raw = filtered_df['raw_delta_days'].mode().iloc[0] if not filtered_df['raw_delta_days'].mode().empty else "N/A"

        avg_busy = filtered_df['busy_delta_days'].mean()
        cv_busy = filtered_df['busy_delta_days'].std() / avg_busy * 100 if avg_busy else 0
        mode_busy = filtered_df['busy_delta_days'].mode().iloc[0] if not filtered_df['busy_delta_days'].mode().empty else "N/A"

        partido_annotation_text = (
            f"General Avg, CV & Mode:<br>"
            f"raw_delta_days: Avg={round(avg_raw, 2)}, CV={round(cv_raw, 2)}%, Mode={mode_raw}<br>"
            f"busy_delta_days: Avg={round(avg_busy, 2)}, CV={round(cv_busy, 2)}%, Mode={mode_busy}"
        )

        visible_array = [
            trace.name.endswith(f"({partido})") for trace in fig.data
        ]

        dropdown_buttons.append({
            'label': partido,
            'method': 'update',
            'args': [
                {'visible': visible_array},  # Update visible traces
                {
                    'title.text': f'Averages for {partido}',
                    'annotations': [
                        {
                            'text': partido_annotation_text,
                            'xref': "paper", 'yref': "paper",
                            'x': 0.5, 'y': 1.15,
                            'showarrow': False,
                            'font': {'size': 12},
                            'align': "center"
                        }
                    ]
                }
            ]
        })

    # Update the layout with dropdown and labels
    fig.update_layout(
        updatemenus=[{
            'buttons': dropdown_buttons,
            'direction': 'down',
            'showactive': True,
            'x': 0.02,  # Dropdown position
            'xanchor': 'left',
            'y': 1.5,
            'yanchor': 'top'
        }],
        title=title,
        xaxis_title="Localidad",
        yaxis_title="Days",
        legend_title="Metrics",
        height=600,  # Taller graph
        template="plotly_white",
        margin=dict(t=100, b=100)  # Adjust margins
    )

    return fig.to_html(full_html=False)