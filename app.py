import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import numpy as np
from data_loader import load_accident_data
from map_utils import (create_base_map, add_accident_markers, create_heatmap, create_blackspot_map, 
                       add_routing_control, add_geocoding_search, add_custom_osm_layers, fit_map_to_df)
from analytics import (calculate_summary_stats, create_temporal_analysis, filter_data,
                       identify_blackspot_zones, analyze_seasonal_patterns, 
                       calculate_year_over_year_trends, generate_risk_predictions, calculate_monthly_trends)
from pathlib import Path

# Resolve data file robustly (works locally and on Streamlit Cloud)
DATA_DIR = Path(__file__).parent / "attached_assets"
CANDIDATES = [
    "RoadTrafficAccidentLocations_last6years.json",   # fallback if you rename
]
def resolve_data_file():
    for name in CANDIDATES:
        p = DATA_DIR / name
        if p.exists():
            return str(p)
    return None

# Page configuration
st.set_page_config(
    page_title="Swiss Road Traffic Accidents Dashboard",
    page_icon="🚴‍♂️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title and introduction
st.title("🚴‍♂️ Swiss Road Traffic ~~Accidents~~ Crashes Dashboard",
         help="The term 'crashes' is used to emphasize the impact on cyclists and pedestrians, as noted in Killed By A Traffic Engineer by Wes Marshall, PE, Phd. book")
st.markdown("""
This dashboard provides comprehensive insights into road traffic accidents across Switzerland, 
with special focus on cyclist safety and risk analysis.
""")

# Load data
@st.cache_data
def get_accident_data():
    file_path = resolve_data_file()
    if not file_path:
        st.error(f"Data file not found in {DATA_DIR}. "
                 f"Found: {[p.name for p in DATA_DIR.glob('*')] if DATA_DIR.exists() else 'no folder'}")
        st.stop()
    return load_accident_data(file_path, use_object_storage=False)


def make_csv_bytes(df, cols):
    return df[cols].to_csv(index=False).encode("utf-8")

try:
    df = get_accident_data()
    
    if df.empty:
        st.error("No accident data available.")
        st.stop()
        
    # Sidebar filters
    st.sidebar.header("🔍 Filters")
    
    # Year filter
    years = sorted(df['AccidentYear'].unique())
    selected_years = st.sidebar.multiselect(
        "Select Years", 
        years, 
        default=years[-3:]  # Default to the most recent year(s)
    )
    
    # Severity filter
    severities = df['AccidentSeverityCategory_en'].unique()
    selected_severities = st.sidebar.multiselect(
        "Accident Severity",
        severities,
        default=None
    )
    
    # Accident type filter
    accident_types = df['AccidentType_en'].unique()
    selected_accident_types = st.sidebar.multiselect(
        "Accident Types",
        accident_types,
        default=None
    )
    
    # Road type filter
    road_types = df['RoadType_en'].unique()
    selected_road_types = st.sidebar.multiselect(
        "Road Types",
        road_types,
        default=None
    )
    
    # Canton filter
    cantons = sorted(df['CantonCode'].unique())
    selected_cantons = st.sidebar.multiselect(
        "Cantons",
        options=cantons,
        default=['ZH'] if 'ZH' in cantons else cantons  
    )
    
    # Involved Parties (multiselect + mode)
    st.sidebar.subheader("Involved Parties")

    PARTY_LABELS = {
        "Pedestrian": "AccidentInvolvingPedestrian",
        "Bicycle": "AccidentInvolvingBicycle",
        "Motorcycle": "AccidentInvolvingMotorcycle",
    }

    selected_parties = st.sidebar.multiselect(
        "Select involved parties",
        options=list(PARTY_LABELS.keys()),
        default=["Bicycle"],
        key="party_multi",
        help="Choose which parties to filter on."
    )

    party_mode = st.sidebar.selectbox(
        "Party filter mode",
        options=["Only selected (exact)", "Any of selected (OR)", "Include all selected (AND)"],
        index=0,
        help=(
            "Only selected (exact): keep rows where ONLY the chosen parties are involved. "
            "Any of selected (OR): keep rows involving at least one of the chosen parties. "
            "Include all selected (AND): keep rows that include all chosen parties (others may also be involved)."
        ),
        key="party_mode"
    )

    # Time filters
    st.sidebar.subheader("Time Filters")
    months = list(range(1, 13))
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    selected_months = st.sidebar.multiselect(
        "Months",
        options=months,
        format_func=lambda x: month_names[x-1],
        default=None
    )
    
    hours = list(range(24))
    selected_hours = st.sidebar.slider(
        "Hour Range",
        0, 23,
        (0, 23)
    )
    
    # Apply filters
    filtered_df = filter_data(
        df, 
        selected_years,
        selected_severities,
        selected_accident_types,
        selected_road_types,
        selected_cantons,
        selected_parties,     
        party_mode,           
        selected_months,
        selected_hours
    )
    
    if filtered_df.empty:
        st.warning("No data matches the selected filters.")
        st.stop()
    
    # Main content
    # Summary statistics
    col1, col2, col3, col4 = st.columns(4)
    st.caption("📊 Sparklines show accident trends by month. ▲/▼ Delta shows change vs. previous month.")
    
    with col1:
        total_trend = calculate_monthly_trends(filtered_df, 'total')
        if total_trend:
            st.metric(
                "Total Accidents", 
                len(filtered_df),
                delta=f"{total_trend['delta']:+d} ({total_trend['delta_pct']:+.1f}%)",
                delta_color="inverse"
            )
            # Sparkline
            fig_spark = go.Figure()
            fig_spark.add_trace(go.Scatter(
                y=total_trend['monthly_values'],
                mode='lines',
                line=dict(color='#1f77b4', width=2),
                fill='tozeroy',
                fillcolor='rgba(31, 119, 180, 0.2)'
            ))
            fig_spark.update_layout(
                height=60,
                margin=dict(l=0, r=0, t=0, b=0),
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
                showlegend=False,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_spark, width='stretch', key='spark_total')
        else:
            st.metric("Total Accidents", len(filtered_df))
    
    with col2:
        fatal_accidents = len(filtered_df[filtered_df['AccidentSeverityCategory'] == 'as1'])
        fatal_trend = calculate_monthly_trends(filtered_df, 'fatal')
        if fatal_trend:
            st.metric(
                "Fatal Accidents", 
                fatal_accidents,
                delta=f"{fatal_trend['delta']:+d} ({fatal_trend['delta_pct']:+.1f}%)",
                delta_color="inverse"
            )
            # Sparkline
            fig_spark = go.Figure()
            fig_spark.add_trace(go.Scatter(
                y=fatal_trend['monthly_values'],
                mode='lines',
                line=dict(color='#d62728', width=2),
                fill='tozeroy',
                fillcolor='rgba(214, 39, 40, 0.2)'
            ))
            fig_spark.update_layout(
                height=60,
                margin=dict(l=0, r=0, t=0, b=0),
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
                showlegend=False,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_spark, width='stretch', key='spark_fatal')
        else:
            st.metric("Fatal Accidents", fatal_accidents)
    
    with col3:
        bicycle_accidents = len(filtered_df[filtered_df['AccidentInvolvingBicycle'] == 'true'])
        bicycle_trend = calculate_monthly_trends(filtered_df, 'bicycle')
        if bicycle_trend:
            st.metric(
                "Bicycle Accidents", 
                bicycle_accidents,
                delta=f"{bicycle_trend['delta']:+d} ({bicycle_trend['delta_pct']:+.1f}%)",
                delta_color="inverse"
            )
            # Sparkline
            fig_spark = go.Figure()
            fig_spark.add_trace(go.Scatter(
                y=bicycle_trend['monthly_values'],
                mode='lines',
                line=dict(color='#ff7f0e', width=2),
                fill='tozeroy',
                fillcolor='rgba(255, 127, 14, 0.2)'
            ))
            fig_spark.update_layout(
                height=60,
                margin=dict(l=0, r=0, t=0, b=0),
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
                showlegend=False,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_spark, width='stretch', key='spark_bicycle')
        else:
            st.metric("Bicycle Accidents", bicycle_accidents)
    
    with col4:
        pedestrian_accidents = len(filtered_df[filtered_df['AccidentInvolvingPedestrian'] == 'true'])
        pedestrian_trend = calculate_monthly_trends(filtered_df, 'pedestrian')
        if pedestrian_trend:
            st.metric(
                "Pedestrian Accidents", 
                pedestrian_accidents,
                delta=f"{pedestrian_trend['delta']:+d} ({pedestrian_trend['delta_pct']:+.1f}%)",
                delta_color="inverse"
            )
            # Sparkline
            fig_spark = go.Figure()
            fig_spark.add_trace(go.Scatter(
                y=pedestrian_trend['monthly_values'],
                mode='lines',
                line=dict(color='#2ca02c', width=2),
                fill='tozeroy',
                fillcolor='rgba(44, 160, 44, 0.2)'
            ))
            fig_spark.update_layout(
                height=60,
                margin=dict(l=0, r=0, t=0, b=0),
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
                showlegend=False,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_spark, width='stretch', key='spark_pedestrian')
        else:
            st.metric("Pedestrian Accidents", pedestrian_accidents)
    
    # Tabs for different views
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["🗺️ Map View", "📊 Analytics", "⏰ Temporal Patterns", "🔥 Hotspots", "🚴 Cyclist Safety", "📋 Data Table"])
    
    with tab1:
        st.subheader("Accident Locations Across Switzerland", 
                     help="""Interactive map showing accident locations with options for heatmap and individual markers. 
                             Reduce filters to see individual markers if too many accidents are present.
                             Click on markers for detailed info.
                     """)

        col1, col2 = st.columns([3, 1])

        with col2:
            map_style = st.selectbox("Map View", ["Normal", "Heatmap"], key="map_style")
            show_markers = st.checkbox("Show Individual Markers", 
                                       value=True,
                                       help="Colors markers by severity. Disable to see heatmap only.",
                                    )

        with col1:
            if map_style == "Heatmap":
                m = create_heatmap(filtered_df)  # uses slim create_base_map()
            else:
                m = create_base_map()
                if show_markers and len(filtered_df) <= 1000:
                    m = add_accident_markers(m, filtered_df)
                elif len(filtered_df) > 1000:
                    st.info(
                        f"Showing heatmap view due to large number of accidents ({len(filtered_df)}). "
                        "Uncheck some filters to see individual markers."
                    )
                    m = create_heatmap(filtered_df)

            # Always zoom to current filtered data
            m = fit_map_to_df(m, filtered_df, lat_col="Latitude", lon_col="Longitude", pad_deg=0.01)

            st_folium(m, use_container_width=True, height=500, key="main_map")
    
    with tab2:
        st.subheader("📊 Accident Analytics")
        
        # Create charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Severity distribution
            severity_counts = filtered_df['AccidentSeverityCategory_en'].value_counts()
            fig_severity = px.pie(
                values=severity_counts.values,
                hole=0.4,
                names=severity_counts.index,
                title="Accident Severity Distribution"
            )
            st.plotly_chart(fig_severity, width='stretch')
        
        with col2:
            # Accident types
            type_counts = filtered_df['AccidentType_en'].value_counts().head(10)
            fig_types = px.bar(
                x=type_counts.values,
                y=type_counts.index,
                color=type_counts.values,
                color_continuous_scale='Reds',
                orientation='h',
                title="Top 10 Accident Types"
            )
            fig_types.update_layout(yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig_types, width='stretch')
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Road type analysis
            road_counts = filtered_df['RoadType_en'].value_counts()
            fig_road = px.bar(
                x=road_counts.index,
                y=road_counts.values,
                color=road_counts.values,
                color_continuous_scale='Blues',
                title="Accidents by Road Type"
            )
            st.plotly_chart(fig_road, width='stretch')
        
        with col2:
            # Canton analysis
            canton_counts = filtered_df['CantonCode'].value_counts().head(10)
            fig_canton = px.bar(
                x=canton_counts.index,
                y=canton_counts.values,
                title="Top 10 Cantons by Accident Count"
            )
            st.plotly_chart(fig_canton, width='stretch')
    
    with tab3:
        st.subheader("⏰ Temporal Patterns")
        
        # Temporal analysis
        col1, col2 = st.columns(2)
        
        with col1:
            # Monthly distribution
            monthly_data = filtered_df.groupby('AccidentMonth').size().reset_index(name='count')
            monthly_data['AccidentMonth'] = monthly_data['AccidentMonth'].astype(int)
            monthly_data['Month'] = monthly_data['AccidentMonth'].map(lambda x: month_names[x-1])
            
            fig_monthly = px.line(
                monthly_data,
                x='Month',
                y='count',
                title="Accidents by Month",
                markers=True
            )
            st.plotly_chart(fig_monthly, width='stretch')
        
        with col2:
            # Hourly distribution
            hourly_data = filtered_df.groupby('AccidentHour').size().reset_index(name='count')
            hourly_data['AccidentHour'] = hourly_data['AccidentHour'].astype(int)
            
            fig_hourly = px.bar(
                hourly_data,
                x='AccidentHour',
                y='count',
                color='count',
                color_continuous_scale='Viridis',
                title="Accidents by Hour of Day"
            )
            st.plotly_chart(fig_hourly, width='stretch')
        
        # Weekly pattern
        weekday_data = filtered_df.groupby('AccidentWeekDay_en').size().reset_index(name='count')
        # Reorder days of week
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        weekday_data['AccidentWeekDay_en'] = pd.Categorical(weekday_data['AccidentWeekDay_en'], categories=day_order, ordered=True)
        weekday_data = weekday_data.sort_values('AccidentWeekDay_en')
        
        fig_weekday = px.bar(
            weekday_data,
            x='AccidentWeekDay_en',
            y='count',
            color='count',
            color_continuous_scale='blues',
            title="Accidents by Day of Week"
        )
        st.plotly_chart(fig_weekday, width='stretch')
        
        # Heatmap: Hour vs Day of Week
        if not filtered_df.empty:
            heatmap_data = filtered_df.groupby(['AccidentWeekDay_en', 'AccidentHour']).size().reset_index(name='count')
            heatmap_pivot = heatmap_data.pivot(index='AccidentWeekDay_en', columns='AccidentHour', values='count').fillna(0)
            
            # Reorder rows
            heatmap_pivot = heatmap_pivot.reindex(day_order)
            
            fig_heatmap = px.imshow(
                heatmap_pivot,
                title="Accident Frequency: Hour vs Day of Week",
                labels=dict(x="Hour", y="Day of Week", color="Count"),
                aspect="auto"
            )
            st.plotly_chart(fig_heatmap, width='stretch')
        
        # Seasonal analysis
        st.subheader("🌦️ Seasonal Patterns")
        
        seasonal_data = analyze_seasonal_patterns(filtered_df.copy())
        
        if seasonal_data and 'accident_counts' in seasonal_data:
            col1, col2 = st.columns(2)
            
            with col1:
                # Accidents by season
                season_df = pd.DataFrame(list(seasonal_data['accident_counts'].items()), 
                                        columns=['Season', 'Count'])
                season_order = ['Winter', 'Spring', 'Summer', 'Fall']
                season_df['Season'] = pd.Categorical(season_df['Season'], categories=season_order, ordered=True)
                season_df = season_df.sort_values('Season')
                
                fig_season = px.bar(
                    season_df,
                    x='Season',
                    y='Count',
                    title="Accidents by Season",
                    color='Count',
                    color_continuous_scale='Blues'
                )
                st.plotly_chart(fig_season, width='stretch')
            
            with col2:
                # Bicycle accidents by season
                if 'bicycle_by_season' in seasonal_data:
                    bike_season_df = pd.DataFrame(list(seasonal_data['bicycle_by_season'].items()), 
                                                  columns=['Season', 'Bicycle Accidents'])
                    bike_season_df['Season'] = pd.Categorical(bike_season_df['Season'], categories=season_order, ordered=True)
                    bike_season_df = bike_season_df.sort_values('Season')
                    
                    fig_bike_season = px.line(
                        bike_season_df,
                        x='Season',
                        y='Bicycle Accidents',
                        title="Bicycle Accidents by Season",
                        markers=True
                    )
                    st.plotly_chart(fig_bike_season, width='stretch')
        
        # Year-over-year trends
        st.subheader("📆 Year-over-Year Trends")
        
        trends_data = calculate_year_over_year_trends(filtered_df.copy())
        
        if trends_data and 'yearly_counts' in trends_data:
            col1, col2 = st.columns(2)
            
            with col1:
                # Overall yearly trend
                yearly_df = pd.DataFrame(list(trends_data['yearly_counts'].items()), 
                                        columns=['Year', 'Accidents'])
                yearly_df = yearly_df.sort_values('Year')
                
                fig_yearly = px.line(
                    yearly_df,
                    x='Year',
                    y='Accidents',
                    title="Total Accidents Over Years",
                    markers=True
                )
                st.plotly_chart(fig_yearly, width='stretch')
            
            with col2:
                # Bicycle trend
                if 'bicycle_yearly' in trends_data:
                    bike_yearly_df = pd.DataFrame(list(trends_data['bicycle_yearly'].items()), 
                                                  columns=['Year', 'Bicycle Accidents'])
                    bike_yearly_df = bike_yearly_df.sort_values('Year')
                    
                    fig_bike_yearly = px.line(
                        bike_yearly_df,
                        x='Year',
                        y='Bicycle Accidents',
                        title="Bicycle Accidents Over Years",
                        markers=True,
                        line_shape='spline'
                    )
                    st.plotly_chart(fig_bike_yearly, width='stretch')
    
    with tab4:
        st.subheader("🔥 Accident Hotspots & Blackspot Zones")
        
        # Clustering parameters
        col1, col2, col3 = st.columns([2, 1, 1])
        with col2:
            cluster_distance = st.slider("Cluster Distance (km)", 0.1, 2.0, 0.5, 0.1)
        with col3:
            min_accidents = st.slider("Min Accidents per Zone", 3, 15, 5, 1)
        
        # Identify blackspot zones using DBSCAN clustering
        blackspots_df = identify_blackspot_zones(filtered_df.copy(), eps_km=cluster_distance, min_samples=min_accidents)
        
        # Display map with blackspot
        st.write("**Identified Blackspot Zones**")
        if not blackspots_df.empty:
            blackspot_map = create_blackspot_map(blackspots_df, basemap_style='opensreetmap')
            st_folium(blackspot_map, width=None, height=400)
        else:
            st.info("No blackspot zones identified with current parameters. Try adjusting the cluster distance or minimum accidents.")
        
        # Display blackspot statistics
        if not blackspots_df.empty:
            st.subheader("Top 10 Blackspot Zones")
            
            display_blackspots = blackspots_df.head(10)[['canton', 'accident_count', 'fatal_accidents', 
                                                          'severe_accidents', 'bicycle_accidents', 
                                                          'most_common_type', 'risk_score']].copy()
            display_blackspots.columns = ['Canton', 'Total', 'Fatal', 'Severe', 'Bicycle', 'Common Type', 'Risk Score']
            st.dataframe(display_blackspots, width='stretch')
        
        # Risk factors analysis
        st.subheader("Risk Factor Analysis")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write("**🚴‍♂️ Cyclist Risk Factors:**")
            bicycle_df = filtered_df[filtered_df['AccidentInvolvingBicycle'] == 'true']
            if not bicycle_df.empty:
                bike_severity = bicycle_df['AccidentSeverityCategory_en'].value_counts()
                for severity, count in bike_severity.items():
                    st.write(f"• {severity}: {count}")
            else:
                st.write("No bicycle accidents in filtered data")
        
        with col2:
            st.write("**🚶‍♂️ Pedestrian Risk Factors:**")
            pedestrian_df = filtered_df[filtered_df['AccidentInvolvingPedestrian'] == 'true']
            if not pedestrian_df.empty:
                ped_severity = pedestrian_df['AccidentSeverityCategory_en'].value_counts()
                for severity, count in ped_severity.items():
                    st.write(f"• {severity}: {count}")
            else:
                st.write("No pedestrian accidents in filtered data")
        
        with col3:
            st.write("**🏍️ Motorcycle Risk Factors:**")
            motorcycle_df = filtered_df[filtered_df['AccidentInvolvingMotorcycle'] == 'true']
            if not motorcycle_df.empty:
                moto_severity = motorcycle_df['AccidentSeverityCategory_en'].value_counts()
                for severity, count in moto_severity.items():
                    st.write(f"• {severity}: {count}")
            else:
                st.write("No motorcycle accidents in filtered data")
    
    with tab5:
        st.subheader("🚴 Cyclist Safety Dashboard")
        
        # Filter for bicycle accidents only
        bicycle_df = filtered_df[filtered_df['AccidentInvolvingBicycle'] == 'true'].copy()
        
        if bicycle_df.empty:
            st.warning("No bicycle accidents found in the filtered data. Adjust filters to see cyclist safety information.")
        else:
            # Key metrics for cyclists
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Bicycle Accidents", len(bicycle_df))
            
            with col2:
                fatal_bike = len(bicycle_df[bicycle_df['AccidentSeverityCategory'] == 'as1'])
                st.metric("Fatal", fatal_bike, delta=None, delta_color="inverse")
            
            with col3:
                severe_bike = len(bicycle_df[bicycle_df['AccidentSeverityCategory'] == 'as2'])
                st.metric("Severe Injuries", severe_bike, delta=None, delta_color="inverse")
            
            with col4:
                light_bike = len(bicycle_df[bicycle_df['AccidentSeverityCategory'] == 'as3'])
                st.metric("Light Injuries", light_bike)
            
            # Risk analysis visualizations
            st.subheader("📈 Cyclist Risk Patterns")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Bicycle accidents by hour
                hourly_bike = bicycle_df.groupby('AccidentHour').size().reset_index(name='count')
                hourly_bike['AccidentHour'] = hourly_bike['AccidentHour'].astype(int)
                
                fig_bike_hour = px.bar(
                    hourly_bike,
                    x='AccidentHour',
                    y='count',
                    title="Bicycle Accidents by Hour of Day",
                    labels={'AccidentHour': 'Hour', 'count': 'Number of Accidents'},
                    color='count',
                    color_continuous_scale='Reds'
                )
                st.plotly_chart(fig_bike_hour, width='stretch')
            
            with col2:
                # Bicycle accidents by day of week
                weekday_bike = bicycle_df.groupby('AccidentWeekDay_en').size().reset_index(name='count')
                day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                weekday_bike['AccidentWeekDay_en'] = pd.Categorical(weekday_bike['AccidentWeekDay_en'], categories=day_order, ordered=True)
                weekday_bike = weekday_bike.sort_values('AccidentWeekDay_en')
                
                fig_bike_day = px.bar(
                    weekday_bike,
                    x='AccidentWeekDay_en',
                    y='count',
                    title="Bicycle Accidents by Day of Week",
                    labels={'AccidentWeekDay_en': 'Day', 'count': 'Number of Accidents'},
                    color='count',
                    color_continuous_scale='Oranges'
                )
                st.plotly_chart(fig_bike_day, width='stretch')
            
            # Road type and accident type analysis
            col1, col2 = st.columns(2)
            
            with col1:
                # Road type for bicycle accidents
                road_bike = bicycle_df['RoadType_en'].value_counts().head(5)
                fig_bike_road = px.pie(
                    values=road_bike.values,
                    hole=0.4,
                    names=road_bike.index,
                    title="Bicycle Accidents by Road Type"
                )
                st.plotly_chart(fig_bike_road, width='stretch')
            
            with col2:
                # Accident types for bicycles
                type_bike = bicycle_df['AccidentType_en'].value_counts().head(5)
                fig_bike_type = px.pie(
                    values=type_bike.values,
                    hole=0.4,
                    names=type_bike.index,
                    title="Most Common Bicycle Accident Types"
                )
                st.plotly_chart(fig_bike_type, width='stretch')
            
            # Bicycle blackspots
            st.subheader("🎯 Bicycle Accident Blackspots")
            
            bicycle_blackspots = identify_blackspot_zones(bicycle_df, eps_km=0.3, min_samples=3)
            
            if not bicycle_blackspots.empty:
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    bike_blackspot_map = create_blackspot_map(bicycle_blackspots, basemap_style='Swiss Topo')
                    st_folium(bike_blackspot_map, width=None, height=400)
                
                with col2:
                    st.write("**Top Cyclist Risk Zones:**")
                    top_bike_spots = bicycle_blackspots.head(5)[['canton', 'accident_count', 'risk_score']]
                    for idx, row in top_bike_spots.iterrows():
                        st.write(f"📍 **{row['canton']}**: {row['accident_count']} accidents (Risk: {row['risk_score']})")
            else:
                st.info("No significant bicycle accident clusters identified in filtered data.")
            
            # Safety recommendations
            st.subheader("💡 Cyclist Safety Recommendations")
            
            # Calculate peak risk times
            peak_hour = bicycle_df['AccidentHour'].mode().iloc[0] if not bicycle_df['AccidentHour'].mode().empty else None
            peak_day = bicycle_df['AccidentWeekDay_en'].mode().iloc[0] if not bicycle_df['AccidentWeekDay_en'].mode().empty else None
            dangerous_road = bicycle_df['RoadType_en'].mode().iloc[0] if not bicycle_df['RoadType_en'].mode().empty else None
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.warning(f"""
                **High-Risk Periods:**
                - Peak accident hour: {peak_hour}:00-{int(peak_hour)+1}:00
                - Highest risk day: {peak_day}
                - Most dangerous roads: {dangerous_road}
                """)
            
            with col2:
                st.success("""
                **Safety Tips:**
                - Use dedicated bike lanes when available
                - Increase visibility with lights and reflective gear
                - Be extra cautious during peak risk hours
                - Plan routes avoiding identified blackspot zones
                """)
            
            # Predictive insights for route planning
            st.subheader("🔮 Predictive Risk Insights for Route Planning")
            
            risk_predictions = generate_risk_predictions(filtered_df.copy())
            
            if risk_predictions:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**⚠️ High-Risk Time/Location Combinations:**")
                    if 'day_hour_risks' in risk_predictions and risk_predictions['day_hour_risks']:
                        risk_df = pd.DataFrame(risk_predictions['day_hour_risks'][:5])
                        risk_df.columns = ['Day', 'Hour', 'Accidents']
                        st.dataframe(risk_df, width='stretch', hide_index=True)
                
                with col2:
                    st.write("**🚴 Cyclist-Specific High-Risk Combinations:**")
                    if 'bicycle_hour_road_risks' in risk_predictions and risk_predictions['bicycle_hour_road_risks']:
                        bike_risk_df = pd.DataFrame(risk_predictions['bicycle_hour_road_risks'][:5])
                        bike_risk_df.columns = ['Hour', 'Road Type', 'Accidents']
                        st.dataframe(bike_risk_df, width='stretch', hide_index=True)
                
                # Route planning recommendations
                if 'recommendations' in risk_predictions and risk_predictions['recommendations']:
                    st.info("**📍 Route Planning Tips:**\n" + "\n".join([f"• {rec}" for rec in risk_predictions['recommendations']]))
    
    with tab6:
        st.subheader("📋 Detailed Accident Data")
        
        # Display options
        col1, col2 = st.columns([3, 1])
        
        with col2:
            show_columns = st.multiselect(
                "Select Columns to Display",
                options=['AccidentUID', 'AccidentType_en', 'AccidentSeverityCategory_en', 
                        'RoadType_en', 'CantonCode', 'AccidentYear', 'AccidentMonth_en',
                        'AccidentWeekDay_en', 'AccidentHour_text', 'AccidentInvolvingBicycle',
                        'AccidentInvolvingPedestrian', 'AccidentInvolvingMotorcycle'],
                default=['AccidentType_en', 'AccidentSeverityCategory_en', 'CantonCode', 
                        'AccidentYear', 'AccidentInvolvingBicycle']
            )
        
        with col1:
            if show_columns:
                display_df = filtered_df[show_columns].copy()

                # Format boolean columns
                for col in ['AccidentInvolvingBicycle', 'AccidentInvolvingPedestrian', 'AccidentInvolvingMotorcycle']:
                    if col in display_df.columns:
                        display_df[col] = display_df[col].map({'true': '✓', 'false': '✗'})

                st.dataframe(display_df, width='stretch', height=400)

                # --- robust download: bytes + stable key ---
                if not display_df.empty:
                    csv_bytes = display_df.to_csv(index=False).encode("utf-8")
                    # make the key stable across re-runs; tie it to columns+rowcount, not transient ids
                    dl_key = f"dl_csv_{'_'.join(show_columns)}_{len(display_df)}"
                    st.download_button(
                        label="Download filtered data as CSV",
                        data=csv_bytes,
                        file_name="swiss_accidents_filtered.csv",
                        mime="text/csv",
                        key=dl_key,
                    )
                else:
                    st.info("No rows to download with current filters.")
            else:
                st.info("Please select columns to display")


    # Footer with insights
    st.markdown("---")
    st.subheader("🎯 Key Insights for Cyclists")
    
    if not filtered_df.empty:
        bicycle_accidents = len(filtered_df[filtered_df['AccidentInvolvingBicycle'] == 'true'])
        total_accidents = len(filtered_df)
        bicycle_percentage = (bicycle_accidents / total_accidents) * 100 if total_accidents > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.info(f"🚴‍♂️ **Bicycle Involvement**: {bicycle_percentage:.1f}% of accidents involve bicycles")
        
        with col2:
            # Peak risk hours for cyclists
            if bicycle_accidents > 0:
                bicycle_df = filtered_df[filtered_df['AccidentInvolvingBicycle'] == 'true']
                peak_hour = bicycle_df['AccidentHour'].mode().iloc[0] if not bicycle_df['AccidentHour'].mode().empty else "N/A"
                st.warning(f"⚠️ **Peak Risk Hour**: {peak_hour}:00-{int(peak_hour)+1 if peak_hour != 'N/A' else 'N/A'}:00 for cyclists")
        
        with col3:
            # Most dangerous road type for cyclists
            if bicycle_accidents > 0:
                bicycle_df = filtered_df[filtered_df['AccidentInvolvingBicycle'] == 'true']
                dangerous_road = bicycle_df['RoadType_en'].mode().iloc[0] if not bicycle_df['RoadType_en'].mode().empty else "N/A"
                st.error(f"🛣️ **High-Risk Roads**: {dangerous_road}")

except Exception as e:
    st.error(f"Error loading or processing data: {str(e)}")
    st.info("Please ensure the data file exists and is properly formatted.")

st.divider()
# Footer with credits and links
st.subheader("🔗 Credits & Links")
st.markdown("""
            Created by @Giovanni Lopez 🚴‍♂️ while attending the 2025 Cycling HACK in Zürich
            Using Streamlit 🚀 Magic, GNU GENERAL PUBLIC LICENSE Version 3, 29 June 2007
            - Event Page: 
                - https://cyclinghack.ch/events/zurich-2025/
            - Dataset opendata.swiss:
                - https://opendata.swiss/en/dataset/polizeilich-registrierte-verkehrsunfalle-auf-dem-stadtgebiet-zurich-seit-2011
                - https://opendata.swiss/en/dataset/polizeilich-registrierte-verkehrsunfalle-auf-dem-stadtgebiet-zurich-seit-2011/resource/d2ba4c0b-3428-47a2-b19d-d6fb2a86814d
            - Who am I?:
                - https://www.linkedin.com/in/giovlopez/
                - https://www.instagram.com/giobcflowy/ 
            - Explore more projects:
                - https://bikeflow.ch
                - https://mapaqua.ch/ (Native App for iOS and Android in development 🙂)
                - https://makinita.ch

            Buy me a coffee ☕: https://buymeacoffee.com/bikeflow
            ,or a two ☕☕: https://www.paypal.com/ncp/payment/CJVK8M6HLW3C2
""")

# Data Disclaimer
st.markdown("""
    <div style='background-color: #f0f2f6; padding: 20px; border-radius: 5px; margin-top: 20px;'>
    <h4 style='margin-top: 0;'>⚠️ Data Disclaimer</h4>
    <p style='font-size: 14px; line-height: 1.6;'>
    This dashboard and its visualizations have been created with the best intentions to provide insights into Swiss road traffic accidents. 
    While reasonable checks and validations have been performed on the data and analysis, the information presented may contain errors, 
    inaccuracies, or incomplete representations.
    </p>
    <p style='font-size: 14px; line-height: 1.6;'>
    <strong>Important:</strong> Before making any decisions, implementing safety measures, or taking actions based on the information 
    provided in this dashboard, users must conduct comprehensive verification, testing, and validation of the data and findings. 
    This tool is intended for informational and analytical purposes only and should not be the sole basis for critical decisions 
    related to road safety, urban planning, or policy making.
    </p>
    <p style='font-size: 14px; line-height: 1.6; margin-bottom: 0;'>
    The creators and maintainers of this dashboard assume no liability for any decisions made or actions taken based on the 
    information presented herein.
    </p>
    </div>
    """, unsafe_allow_html=True)