import plotly.graph_objects as go
import pandas as pd
import numpy as np

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
    filtered_df.loc[filtered_df['responsibility'] == 'transporte', 'type'] = '02_visitado'
    filtered_df.loc[filtered_df['type'] == 'failed', 'type'] = '03_fallido'
    filtered_df.loc[filtered_df['type'] == 'completed', 'type'] = '01_completado'

    filtered_df = (
    filtered_df.groupby(['month', 'type'])
    .agg({'percentage': 'sum'})  # Aggregate percentages across all sellers if no specific seller
    .reset_index()
    )

    # Pivot the data for plotting
    pivot_table = filtered_df.pivot(index='month', columns='type', values='percentage').fillna(0)

    color_map = {
    '01_completado': '#636efa',
    '02_visitado': '#08cc94',
    '03_fallido': '#ef553b'
    }
    

    # Create traces for each type
    fig = go.Figure()
    for col in pivot_table.columns:
        fig.add_trace(go.Bar(
            x=pivot_table.index,
            y=pivot_table[col],
            name=col,
            hoverinfo="x+y+name",
            text=round(pivot_table[col],2 ),
            textposition='inside',
            marker=dict(color=color_map[col])
        ))

    # for category in filtered_df['type'].unique():
    #     fig.add_trace(go.Bar(
    #         x=filtered_df[filtered_df['type'] == category]['month'],  # Filtered x-values
    #         y=filtered_df[filtered_df['type'] == category]['percentage'],  # Filtered y-values
    #         name=category,
    #         marker=dict(color=color_map[category])
    #         )
    #         )

    # Update layout for better visualization
    fig.update_layout(
        barmode='stack',
        title="Efectividad entregas AMBA",
        xaxis=dict(
        title="Mes",
        type="category",  # Force x-axis to be categorical
        tickformat='%b %Y'
        ),
        yaxis_title="Porcentaje (%)",
        legend_title="Tipo",
        template="plotly_white",
        margin=dict(l=40, r=40, t=40, b=40),
        hovermode="x unified",
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
            hoverinfo="x+y+name",
            text=round(pivot_table[col],2 ),
            textposition='inside'
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
            hoverinfo="x+y+name",
            text=round(pivot_table[col],2 ),
            textposition='inside'
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


def create_bar_chart(df0, group_col, y_col, title):
    df = df0.sort_values(by=y_col, ascending=False)
    fig = go.Figure()
    
    # Create bar traces
    for y in y_col:
        fig.add_trace(go.Bar(
            x=df[group_col],
            y=df[y],
            name=y,
            hoverinfo="x+y+name",
            text=round(df[y],2 ),
            textposition='inside'
        ))

    # Calculate stats for each metric
    stats_texts = ["Promedio general, Coeficiente de variacon & Moda:"]
    for y in y_col:
        avg = df[y].mean()
        cv = (df[y].std() / avg * 100) if avg else 0
        mode = df[y].mode().iloc[0] if not df[y].mode().empty else "N/A"
        stats_texts.append(f"{y}: Promedio={round(avg, 2)}, CV={round(cv, 2)}%, Moda={round(mode, 2)}")
    
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
        legend_title="Metricas",
        template="plotly_white",
        height=600,  # Adjusted height
        margin=dict(t=100, b=100)  # Adjusted margins for annotations
    )

    return fig.to_html(full_html=False)


def create_filtered_chart(df0, group_col, sub_group_col, y_col, title, raws_col="raw_delta_days", busy_col='busy_delta_days'):
    df = df0.sort_values(by=busy_col, ascending=False)
    partidos = np.sort(df[group_col].unique())

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
                visible=(partido == partidos[0]),  # Show only the first partido by default
                text=round(filtered_df[y], 2),
                textposition='inside'
            ))

    # Calculate general stats for "All Partidos"
    general_avg_raw = df[raws_col].mean()
    general_cv_raw = df[raws_col].std() / general_avg_raw * 100 if general_avg_raw else 0
    general_mode_raw = df[raws_col].mode().iloc[0] if not df[raws_col].mode().empty else "N/A"

    general_avg_busy = df[busy_col].mean()
    general_cv_busy = df[busy_col].std() / general_avg_busy * 100 if general_avg_busy else 0
    general_mode_busy = df[busy_col].mode().iloc[0] if not df[busy_col].mode().empty else "N/A"

    # Create a default annotation for "All Partidos"
    annotation_text = (
        f"Promedio general, Coeficiente de variacon & Moda:<br>"
        f"Dias corridos: Promedio={round(general_avg_raw, 2)}, CV={round(general_cv_raw, 2)}%, Moda={round(general_mode_raw, 2)}<br>"
        f"Dias laboral: Promedio={round(general_avg_busy, 2)}, CV={round(general_cv_busy, 2)}%, Moda={round(general_mode_busy, 2)}"
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
        avg_raw = filtered_df[raws_col].mean()
        cv_raw = filtered_df[raws_col].std() / avg_raw * 100 if avg_raw else 0
        mode_raw = filtered_df[raws_col].mode().iloc[0] if not filtered_df[raws_col].mode().empty else "N/A"

        avg_busy = filtered_df[busy_col].mean()
        cv_busy = filtered_df[busy_col].std() / avg_busy * 100 if avg_busy else 0
        mode_busy = filtered_df[busy_col].mode().iloc[0] if not filtered_df[busy_col].mode().empty else "N/A"

        partido_annotation_text = (
            f"Promedio general, Coeficiente de variacon & Moda:<br>"
            f"Dias corridos: Promedio={round(avg_raw, 2)}, CV={round(cv_raw, 2)}%, Moda={round(mode_raw, 2)}<br>"
            f"Dias laborales: Promedio={round(avg_busy, 2)}, CV={round(cv_busy, 2)}%, Moda={round(mode_busy, 2)}"
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
                    'title.text': f'Promedio por {partido}',
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
        legend_title="Metricas",
        height=600,  # Taller graph
        template="plotly_white",
        margin=dict(t=100, b=100)  # Adjust margins
    )

    return fig.to_html(full_html=False)


def plot_cumulative_percentage(df1, col1, df2, col2):
    """
    Plots a line graph for cumulative_percentage vs. raw_delta_days (for df1) and busy_delta_days (for df2).
    Fills the area under the curve.
    
    Parameters:
    - df1: First DataFrame containing raw_delta_days and cumulative_percentage.
    - df2: Second DataFrame containing busy_delta_days and cumulative_percentage.
    - col1: The name of the column in df1 representing the x-axis values (e.g., 'raw_delta_days').
    - col2: The name of the column in df2 representing the x-axis values (e.g., 'busy_delta_days').
    """
    
    # Sort both DataFrames by their respective x-axis columns (if not already sorted)
    df1 = df1.sort_values(by=col1)
    df2 = df2.sort_values(by=col2)
    
    # Create the plot
    fig = go.Figure()
    
    # Add the first line (raw_delta_days vs cumulative_percentage)
    fig.add_trace(go.Scatter(
        x=df1[col1], 
        y=df1['cumulative_percentage'], 
        mode='lines', 
        name='Delta dias corrido', 
        fill='tozeroy',  # Fills the area under the line
        fillcolor='rgba(0, 100, 255, 0.3)',  # Semi-transparent blue
        line=dict(color='blue'),
    ))
    
    # Add the second line (busy_delta_days vs cumulative_percentage)
    fig.add_trace(go.Scatter(
        x=df2[col2], y=df2['cumulative_percentage'], 
        mode='lines', 
        name='Delta dias laborales', 
        fill='tozeroy',  # Fills the area under the line
        fillcolor='rgba(255, 100, 0, 0.3)',  # Semi-transparent orange
        line=dict(color='orange')
    ))
    
    # Customize layout
    fig.update_layout(
        title='Porcentage acumulativo por dias',
        xaxis_title='Dias',
        yaxis_title='Porcentaje acomulado',
        template='plotly_white'  # Optional: dark mode styling
    )
    
    return fig.to_html(full_html=False)


def plot_box_plots(raw_df, raw_col, busy_df, busy_col):
    """
    Plots horizontal box plots for raw_delta_days and busy_delta_days based on frequency.
    
    Parameters:
    - raw_df: The DataFrame with raw_delta_days and corresponding frequencies.
    - raw_col: The column name for the raw data.
    - busy_df: The DataFrame with busy_delta_days and corresponding frequencies.
    - busy_col: The column name for the busy data.
    
    Returns:
    - Plotly horizontal box plot figure.
    """
    # Prepare data for box plot
    raw_data = raw_df[raw_col]
    busy_data = busy_df[busy_col]
    
    # Create the figure
    fig = go.Figure()
    
    # Add horizontal box plot for raw_delta_days
    fig.add_trace(go.Box(
        x=raw_data,  # Plot raw data along x-axis
        name="Delta dias corrido",
        boxmean='sd',  # Show mean and standard deviation
        marker=dict(color='blue'),
        orientation='h'  # Horizontal box plot
    ))
    
    # Add horizontal box plot for busy_delta_days
    fig.add_trace(go.Box(
        x=busy_data,  # Plot busy data along x-axis
        name="Delta dias laborales",
        boxmean='sd',  # Show mean and standard deviation
        marker=dict(color='orange'),
        orientation='h'  # Horizontal box plot
    ))

    # Update layout with titles and labels
    fig.update_layout(
        title="Diagrama de cajas frecuencial de dias de corrido vs dias laborales",
        xaxis_title="Dias frequencia",  # X-axis now represents frequency
        yaxis_title="Tipo medida",    # Y-axis represents the type of days (Raw or Busy)
        template='plotly_white'
    )
    
    return fig.to_html(full_html=False)


def plot_relative_volume_bar(df, province_col, order_col, title="Volumen relativo de ordenes por povincia"):
    """
    Plots a bar chart for relative volume of orders per province as percentages.
    
    Parameters:
    - df (pandas.DataFrame): The dataframe with 'codigoPostal__provincia' and 'relative_percentage' columns.
    - province_col (str): The column name for provinces (e.g., 'codigoPostal__provincia').
    - order_col (str): The column name for relative percentages (e.g., 'relative_percentage').
    
    Returns:
    - Plotly bar chart figure.
    """
    # Prepare data for the bar plot
    provinces = df[province_col]
    relative_percentages = df[order_col]
    
    # Create the figure
    fig = go.Figure()

    # Add a bar plot for the relative percentages of orders
    fig.add_trace(go.Bar(
        x=provinces,  # Provinces on x-axis
        y=relative_percentages,  # Relative percentages on y-axis
        marker=dict(color='royalblue'),
        name="Relative Volume of Orders",
        text=round(relative_percentages, 2),
        textposition='inside'
    ))

    # Update layout with titles and labels
    fig.update_layout(
        title=title,
        xaxis_title="Provincia",
        yaxis_title="Porcentage relativo (%)",
        template='plotly_white',
        xaxis_tickangle=45  # Rotate x-axis labels for readability
    )
    
    return fig.to_html(full_html=False)


def plot_tipo_percentage_bar_chart(df, province_col, tipo_col, percentage_col):
    """
    Creates a grouped bar chart comparing percentages of DIST and SUCA for each province,
    with average annotations.

    Parameters:
    - df: DataFrame containing the data.
    - province_col: Column name for provinces.
    - tipo_col: Column name for tipo (DIST, SUCA).
    - percentage_col: Column name for percentages.

    Returns:
    - Plotly figure in HTML format.
    """
    # Separate data for DIST and SUCA
    dist_df = df[df[tipo_col] == "DIST"]
    suca_df = df[df[tipo_col] == "SUCA"]
    
    # Calculate averages
    avg_dist = dist_df[percentage_col].mean()
    avg_suca = suca_df[percentage_col].mean()
    
    # Create the plot
    fig = go.Figure()
    
    # Add bar for DIST
    fig.add_trace(go.Bar(
        x=dist_df[province_col],
        y=dist_df[percentage_col],
        name="DIST",
        marker=dict(color="blue"),
        text=round(dist_df[percentage_col], 2),
        textposition='inside'
    ))
    
    # Add bar for SUCA
    fig.add_trace(go.Bar(
        x=suca_df[province_col],
        y=suca_df[percentage_col],
        name="SUCA",
        marker=dict(color="orange"),
        text=round(suca_df[percentage_col], 2),
        textposition='inside'
    ))
    
    # Add average annotations
    avg_text = (
        f"Promedio DIST: {avg_dist:.2f}%<br>"
        f"Promedio SUCA: {avg_suca:.2f}%"
    )
    fig.add_annotation(
        text=avg_text,
        xref="paper", yref="paper",
        x=0.5, y=1.15,  # Centered above the graph
        showarrow=False,
        font=dict(size=12),
        align="center"
    )
    
    # Update layout
    fig.update_layout(
        barmode="group",  # Grouped bar chart
        title="Percentage Comparison of DIST and SUCA by Province",
        xaxis_title="Provincia",
        yaxis_title="Porcentaje",
        legend_title="Tipo",
        template="plotly_white",
        margin=dict(t=100)  # Adjust margin for annotation space
    )
    
    return fig.to_html(full_html=False)


def plot_hierarchical_bar_chart(df, primary_col, secondary_col, value_col, title="Hierarchical Bar Chart"):
    """
    Plots a hierarchical bar chart where each primary category on the X-axis is subdivided into secondary categories.

    Parameters:
    - df (pandas.DataFrame): The dataframe with the data to plot.
    - primary_col (str): The column name for primary categories (e.g., months).
    - secondary_col (str): The column name for secondary categories (e.g., product types).
    - value_col (str): The column name for the values to plot (e.g., sales or percentages).
    - title (str): The title of the chart.

    Returns:
    - Plotly bar chart figure as HTML.
    """
    # Ensure primary_col is sorted
    df = df.sort_values(by=[primary_col, secondary_col])
    
    # Get unique primary categories (e.g., months) and secondary categories (e.g., product types)
    primary_categories = df[primary_col].unique()
    secondary_categories = df[secondary_col].unique()

    # Create the figure
    fig = go.Figure()

    # Add a trace for each secondary category
    for subcat in secondary_categories:
        filtered_df = df[df[secondary_col] == subcat]
        fig.add_trace(go.Bar(
            x=filtered_df[primary_col],
            y=filtered_df[value_col],
            name=subcat,
            text=round(filtered_df[value_col], 2),
            textposition='inside'
        ))

    # Update layout for the hierarchical structure
    fig.update_layout(
        barmode='group',  # Group bars for each primary category
        title=title,
        xaxis_title=primary_col.capitalize(),
        yaxis_title=value_col.capitalize(),
        legend_title=secondary_col.capitalize(),
        template='plotly_white',
        xaxis_tickangle=45,  # Rotate x-axis labels for readability
        height=600  # Adjust height for better visualization
    )

    return fig.to_html(full_html=False)