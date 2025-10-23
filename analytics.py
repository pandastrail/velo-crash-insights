import pandas as pd
import numpy as np
from datetime import datetime
from scipy.spatial import distance
from sklearn.cluster import DBSCAN

def calculate_summary_stats(df):
    """
    Calculate comprehensive summary statistics for accident data.
    
    Args:
        df (pandas.DataFrame): Accident data
        
    Returns:
        dict: Summary statistics
    """
    if df.empty:
        return {}
    
    stats = {}
    
    # Basic counts
    stats['total_accidents'] = len(df)
    stats['unique_cantons'] = df['CantonCode'].nunique() if 'CantonCode' in df.columns else 0
    stats['date_range'] = {
        'start_year': int(df['AccidentYear'].min()) if 'AccidentYear' in df.columns else None,
        'end_year': int(df['AccidentYear'].max()) if 'AccidentYear' in df.columns else None
    }
    
    # Severity distribution
    if 'AccidentSeverityCategory_en' in df.columns:
        stats['severity_distribution'] = df['AccidentSeverityCategory_en'].value_counts().to_dict()
    
    # Accident types
    if 'AccidentType_en' in df.columns:
        stats['top_accident_types'] = df['AccidentType_en'].value_counts().head(5).to_dict()
    
    # Involved parties
    if 'AccidentInvolvingBicycle' in df.columns:
        stats['bicycle_accidents'] = len(df[df['AccidentInvolvingBicycle'] == 'true'])
        stats['bicycle_percentage'] = (stats['bicycle_accidents'] / stats['total_accidents']) * 100
    
    if 'AccidentInvolvingPedestrian' in df.columns:
        stats['pedestrian_accidents'] = len(df[df['AccidentInvolvingPedestrian'] == 'true'])
        stats['pedestrian_percentage'] = (stats['pedestrian_accidents'] / stats['total_accidents']) * 100
    
    if 'AccidentInvolvingMotorcycle' in df.columns:
        stats['motorcycle_accidents'] = len(df[df['AccidentInvolvingMotorcycle'] == 'true'])
        stats['motorcycle_percentage'] = (stats['motorcycle_accidents'] / stats['total_accidents']) * 100
    
    # Road type analysis
    if 'RoadType_en' in df.columns:
        stats['road_type_distribution'] = df['RoadType_en'].value_counts().to_dict()
    
    # Canton analysis
    if 'CantonCode' in df.columns:
        stats['top_cantons'] = df['CantonCode'].value_counts().head(10).to_dict()
    
    return stats

def create_temporal_analysis(df):
    """
    Analyze temporal patterns in accident data.
    
    Args:
        df (pandas.DataFrame): Accident data
        
    Returns:
        dict: Temporal analysis results
    """
    if df.empty:
        return {}
    
    temporal_stats = {}
    
    # Monthly analysis
    if 'AccidentMonth' in df.columns:
        monthly_counts = df.groupby('AccidentMonth').size()
        temporal_stats['monthly_distribution'] = monthly_counts.to_dict()
        temporal_stats['peak_month'] = monthly_counts.idxmax()
        temporal_stats['lowest_month'] = monthly_counts.idxmin()
    
    # Hourly analysis
    if 'AccidentHour' in df.columns:
        hourly_counts = df.groupby('AccidentHour').size()
        temporal_stats['hourly_distribution'] = hourly_counts.to_dict()
        temporal_stats['peak_hour'] = hourly_counts.idxmax()
        temporal_stats['safest_hour'] = hourly_counts.idxmin()
    
    # Day of week analysis
    if 'AccidentWeekDay_en' in df.columns:
        weekday_counts = df.groupby('AccidentWeekDay_en').size()
        temporal_stats['weekday_distribution'] = weekday_counts.to_dict()
        temporal_stats['peak_weekday'] = weekday_counts.idxmax()
        temporal_stats['safest_weekday'] = weekday_counts.idxmin()
    
    # Yearly trends
    if 'AccidentYear' in df.columns:
        yearly_counts = df.groupby('AccidentYear').size()
        temporal_stats['yearly_distribution'] = yearly_counts.to_dict()
        
        # Calculate trend
        years = list(yearly_counts.index)
        counts = list(yearly_counts.values)
        if len(years) > 1:
            trend_slope = np.polyfit(years, counts, 1)[0]
            temporal_stats['yearly_trend'] = 'increasing' if trend_slope > 0 else 'decreasing'
            temporal_stats['trend_slope'] = trend_slope
    
    return temporal_stats

def filter_data(df, years=None, severities=None, accident_types=None, road_types=None, 
                cantons=None, show_pedestrian=True, show_bicycle=True, show_motorcycle=True,
                months=None, hour_range=None):
    """
    Apply comprehensive filters to accident data.
    
    Args:
        df (pandas.DataFrame): Accident data
        years (list): Years to include
        severities (list): Severity categories to include
        accident_types (list): Accident types to include
        road_types (list): Road types to include
        cantons (list): Cantons to include
        show_pedestrian (bool): Include pedestrian accidents
        show_bicycle (bool): Include bicycle accidents
        show_motorcycle (bool): Include motorcycle accidents
        months (list): Months to include (1-12)
        hour_range (tuple): Hour range (start, end)
        
    Returns:
        pandas.DataFrame: Filtered data
    """
    filtered_df = df.copy()
    
    # Year filter
    if years and 'AccidentYear' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['AccidentYear'].isin(years)]
    
    # Severity filter
    if severities and 'AccidentSeverityCategory_en' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['AccidentSeverityCategory_en'].isin(severities)]
    
    # Accident type filter
    if accident_types and 'AccidentType_en' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['AccidentType_en'].isin(accident_types)]
    
    # Road type filter
    if road_types and 'RoadType_en' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['RoadType_en'].isin(road_types)]
    
    # Canton filter
    if cantons and 'CantonCode' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['CantonCode'].isin(cantons)]
    
    # Involved parties filter
    party_conditions = []
    if show_pedestrian and 'AccidentInvolvingPedestrian' in filtered_df.columns:
        party_conditions.append(filtered_df['AccidentInvolvingPedestrian'] == 'true')
    if show_bicycle and 'AccidentInvolvingBicycle' in filtered_df.columns:
        party_conditions.append(filtered_df['AccidentInvolvingBicycle'] == 'true')
    if show_motorcycle and 'AccidentInvolvingMotorcycle' in filtered_df.columns:
        party_conditions.append(filtered_df['AccidentInvolvingMotorcycle'] == 'true')
    
    # If none of the party types are selected, show all
    if not (show_pedestrian or show_bicycle or show_motorcycle):
        pass  # Show all
    elif party_conditions:
        # Combine conditions with OR
        combined_condition = party_conditions[0]
        for condition in party_conditions[1:]:
            combined_condition = combined_condition | condition
        
        # Also include accidents that don't involve any of these parties
        no_special_parties = (
            (filtered_df['AccidentInvolvingPedestrian'] == 'false') &
            (filtered_df['AccidentInvolvingBicycle'] == 'false') &
            (filtered_df['AccidentInvolvingMotorcycle'] == 'false')
        )
        
        filtered_df = filtered_df[combined_condition | no_special_parties]
    
    # Month filter
    if months and 'AccidentMonth' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['AccidentMonth'].isin(months)]
    
    # Hour range filter
    if hour_range and 'AccidentHour' in filtered_df.columns:
        start_hour, end_hour = hour_range
        filtered_df = filtered_df[
            (filtered_df['AccidentHour'] >= start_hour) & 
            (filtered_df['AccidentHour'] <= end_hour)
        ]
    
    return filtered_df

def calculate_risk_metrics(df):
    """
    Calculate risk metrics for different categories.
    
    Args:
        df (pandas.DataFrame): Accident data
        
    Returns:
        dict: Risk metrics
    """
    if df.empty:
        return {}
    
    risk_metrics = {}
    
    # Overall risk by severity
    total_accidents = len(df)
    if 'AccidentSeverityCategory' in df.columns:
        fatal_rate = len(df[df['AccidentSeverityCategory'] == 'as1']) / total_accidents * 100
        severe_rate = len(df[df['AccidentSeverityCategory'] == 'as2']) / total_accidents * 100
        
        risk_metrics['fatal_accident_rate'] = fatal_rate
        risk_metrics['severe_accident_rate'] = severe_rate
    
    # Risk by road type
    if 'RoadType_en' in df.columns:
        road_risk = df.groupby('RoadType_en').agg({
            'AccidentSeverityCategory': lambda x: (x == 'as1').sum() / len(x) * 100 if len(x) > 0 else 0
        }).round(2)
        risk_metrics['road_type_fatal_rates'] = road_risk.to_dict()['AccidentSeverityCategory']
    
    # Risk by time of day
    if 'AccidentHour' in df.columns:
        hourly_risk = df.groupby('AccidentHour').agg({
            'AccidentSeverityCategory': lambda x: (x.isin(['as1', 'as2'])).sum() / len(x) * 100 if len(x) > 0 else 0
        }).round(2)
        risk_metrics['hourly_severe_rates'] = hourly_risk.to_dict()['AccidentSeverityCategory']
    
    # Bicycle-specific risks
    if 'AccidentInvolvingBicycle' in df.columns:
        bicycle_df = df[df['AccidentInvolvingBicycle'] == 'true']
        if not bicycle_df.empty:
            bicycle_fatal_rate = len(bicycle_df[bicycle_df['AccidentSeverityCategory'] == 'as1']) / len(bicycle_df) * 100
            risk_metrics['bicycle_fatal_rate'] = bicycle_fatal_rate
            
            # Peak risk hours for cyclists
            if 'AccidentHour' in bicycle_df.columns:
                bicycle_hourly = bicycle_df.groupby('AccidentHour').size()
                risk_metrics['bicycle_peak_hours'] = bicycle_hourly.nlargest(3).index.tolist()
    
    return risk_metrics

def generate_insights(df):
    """
    Generate data-driven insights from accident data.
    
    Args:
        df (pandas.DataFrame): Accident data
        
    Returns:
        list: List of insight strings
    """
    if df.empty:
        return ["No data available for analysis."]
    
    insights = []
    
    # Basic statistics insights
    total_accidents = len(df)
    insights.append(f"Dataset contains {total_accidents:,} traffic accidents across Switzerland.")
    
    # Severity insights
    if 'AccidentSeverityCategory_en' in df.columns:
        severity_counts = df['AccidentSeverityCategory_en'].value_counts()
        most_common_severity = severity_counts.index[0]
        insights.append(f"Most accidents result in {most_common_severity.lower()} ({severity_counts.iloc[0]:,} cases).")
        
        if 'Accident with fatal outcome' in severity_counts:
            fatal_count = severity_counts['Accident with fatal outcome']
            fatal_rate = (fatal_count / total_accidents) * 100
            insights.append(f"Fatal accidents account for {fatal_rate:.1f}% of all accidents.")
    
    # Bicycle safety insights
    if 'AccidentInvolvingBicycle' in df.columns:
        bicycle_accidents = len(df[df['AccidentInvolvingBicycle'] == 'true'])
        bicycle_rate = (bicycle_accidents / total_accidents) * 100
        insights.append(f"Bicycles are involved in {bicycle_rate:.1f}% of all accidents ({bicycle_accidents:,} cases).")
        
        bicycle_df = df[df['AccidentInvolvingBicycle'] == 'true']
        if not bicycle_df.empty and 'AccidentHour' in bicycle_df.columns:
            peak_hour = bicycle_df['AccidentHour'].mode().iloc[0]
            insights.append(f"Peak risk hour for cyclists is {peak_hour}:00-{peak_hour+1}:00.")
    
    # Temporal insights
    if 'AccidentWeekDay_en' in df.columns:
        weekday_counts = df['AccidentWeekDay_en'].value_counts()
        dangerous_day = weekday_counts.index[0]
        insights.append(f"{dangerous_day} has the highest number of accidents ({weekday_counts.iloc[0]:,} cases).")
    
    # Geographic insights
    if 'CantonCode' in df.columns:
        canton_counts = df['CantonCode'].value_counts()
        top_canton = canton_counts.index[0]
        insights.append(f"Canton {top_canton} reports the most accidents ({canton_counts.iloc[0]:,} cases).")
    
    # Road type insights
    if 'RoadType_en' in df.columns:
        road_counts = df['RoadType_en'].value_counts()
        dangerous_road_type = road_counts.index[0]
        insights.append(f"Most accidents occur on {dangerous_road_type.lower()}s ({road_counts.iloc[0]:,} cases).")
    
    return insights

def identify_blackspot_zones(df, eps_km=0.5, min_samples=5):
    """
    Identify accident blackspot zones using DBSCAN clustering.
    
    Args:
        df (pandas.DataFrame): Accident data with latitude and longitude
        eps_km (float): Maximum distance (in km) between points to be in same cluster
        min_samples (int): Minimum number of accidents to form a blackspot
        
    Returns:
        pandas.DataFrame: DataFrame with cluster assignments and statistics
    """
    if df.empty or len(df) < min_samples:
        return pd.DataFrame()
    
    # Extract coordinates
    coords = df[['latitude', 'longitude']].values
    
    # Convert eps from km to degrees (rough approximation: 1 degree ≈ 111 km)
    eps_degrees = eps_km / 111.0
    
    # Perform DBSCAN clustering
    clustering = DBSCAN(eps=eps_degrees, min_samples=min_samples, metric='euclidean')
    df['cluster'] = clustering.fit_predict(coords)
    
    # Analyze clusters (exclude noise points with cluster = -1)
    blackspots = []
    
    for cluster_id in df['cluster'].unique():
        if cluster_id == -1:
            continue
            
        cluster_data = df[df['cluster'] == cluster_id]
        
        # Calculate cluster statistics
        center_lat = cluster_data['latitude'].mean()
        center_lon = cluster_data['longitude'].mean()
        accident_count = len(cluster_data)
        
        # Severity breakdown
        fatal_count = len(cluster_data[cluster_data['AccidentSeverityCategory'] == 'as1'])
        severe_count = len(cluster_data[cluster_data['AccidentSeverityCategory'] == 'as2'])
        light_count = len(cluster_data[cluster_data['AccidentSeverityCategory'] == 'as3'])
        
        # Bicycle involvement
        bicycle_count = len(cluster_data[cluster_data['AccidentInvolvingBicycle'] == 'true'])
        
        # Most common canton
        canton = cluster_data['CantonCode'].mode().iloc[0] if not cluster_data['CantonCode'].mode().empty else 'Unknown'
        
        # Most common accident type
        accident_type = cluster_data['AccidentType_en'].mode().iloc[0] if 'AccidentType_en' in cluster_data.columns and not cluster_data['AccidentType_en'].mode().empty else 'Unknown'
        
        blackspots.append({
            'cluster_id': cluster_id,
            'center_lat': center_lat,
            'center_lon': center_lon,
            'accident_count': accident_count,
            'fatal_accidents': fatal_count,
            'severe_accidents': severe_count,
            'light_accidents': light_count,
            'bicycle_accidents': bicycle_count,
            'canton': canton,
            'most_common_type': accident_type,
            'risk_score': fatal_count * 5 + severe_count * 3 + light_count * 1
        })
    
    blackspots_df = pd.DataFrame(blackspots)
    
    # Sort by risk score
    if not blackspots_df.empty:
        blackspots_df = blackspots_df.sort_values('risk_score', ascending=False)
    
    return blackspots_df

def analyze_seasonal_patterns(df):
    """
    Analyze seasonal patterns in accident data.
    
    Args:
        df (pandas.DataFrame): Accident data
        
    Returns:
        dict: Seasonal analysis results
    """
    if df.empty or 'AccidentMonth' not in df.columns:
        return {}
    
    seasonal_stats = {}
    
    # Define seasons (Northern Hemisphere)
    seasons = {
        'Winter': [12, 1, 2],
        'Spring': [3, 4, 5],
        'Summer': [6, 7, 8],
        'Fall': [9, 10, 11]
    }
    
    # Count accidents by season
    df['season'] = df['AccidentMonth'].apply(
        lambda m: next((season for season, months in seasons.items() if m in months), 'Unknown')
    )
    
    season_counts = df.groupby('season').size().to_dict()
    seasonal_stats['accident_counts'] = season_counts
    
    # Severity by season
    if 'AccidentSeverityCategory_en' in df.columns:
        severity_by_season = df.groupby(['season', 'AccidentSeverityCategory_en']).size().unstack(fill_value=0)
        seasonal_stats['severity_by_season'] = severity_by_season.to_dict()
    
    # Bicycle accidents by season
    if 'AccidentInvolvingBicycle' in df.columns:
        bicycle_seasonal = df[df['AccidentInvolvingBicycle'] == 'true'].groupby('season').size().to_dict()
        seasonal_stats['bicycle_by_season'] = bicycle_seasonal
    
    return seasonal_stats

def calculate_year_over_year_trends(df):
    """
    Calculate year-over-year trends in accident data.
    
    Args:
        df (pandas.DataFrame): Accident data
        
    Returns:
        dict: Year-over-year trend analysis
    """
    if df.empty or 'AccidentYear' not in df.columns:
        return {}
    
    trends = {}
    
    # Overall yearly trend
    yearly_counts = df.groupby('AccidentYear').size().sort_index()
    trends['yearly_counts'] = yearly_counts.to_dict()
    
    # Calculate percentage change
    if len(yearly_counts) > 1:
        pct_changes = yearly_counts.pct_change() * 100
        trends['yearly_pct_change'] = pct_changes.to_dict()
    
    # Bicycle trends
    if 'AccidentInvolvingBicycle' in df.columns:
        bicycle_yearly = df[df['AccidentInvolvingBicycle'] == 'true'].groupby('AccidentYear').size().sort_index()
        trends['bicycle_yearly'] = bicycle_yearly.to_dict()
    
    # Severity trends
    if 'AccidentSeverityCategory' in df.columns:
        fatal_yearly = df[df['AccidentSeverityCategory'] == 'as1'].groupby('AccidentYear').size().sort_index()
        trends['fatal_yearly'] = fatal_yearly.to_dict()
    
    return trends

def generate_risk_predictions(df):
    """
    Generate predictive insights for high-risk time/location combinations.
    
    Args:
        df (pandas.DataFrame): Accident data
        
    Returns:
        dict: Risk predictions and recommendations
    """
    if df.empty:
        return {}
    
    predictions = {}
    
    # High-risk time/location combinations
    if all(col in df.columns for col in ['AccidentHour', 'CantonCode', 'AccidentWeekDay_en']):
        # Find most dangerous hour/canton combinations
        hour_canton = df.groupby(['AccidentHour', 'CantonCode']).size().reset_index(name='count')
        hour_canton = hour_canton.sort_values('count', ascending=False).head(10)
        predictions['hour_canton_risks'] = hour_canton.to_dict('records')
        
        # Find most dangerous day/hour combinations
        day_hour = df.groupby(['AccidentWeekDay_en', 'AccidentHour']).size().reset_index(name='count')
        day_hour = day_hour.sort_values('count', ascending=False).head(10)
        predictions['day_hour_risks'] = day_hour.to_dict('records')
    
    # Bicycle-specific risk predictions
    if 'AccidentInvolvingBicycle' in df.columns:
        bicycle_df = df[df['AccidentInvolvingBicycle'] == 'true']
        
        if not bicycle_df.empty and all(col in bicycle_df.columns for col in ['AccidentHour', 'RoadType_en', 'CantonCode']):
            # High-risk hour/road combinations for cyclists
            bike_hour_road = bicycle_df.groupby(['AccidentHour', 'RoadType_en']).size().reset_index(name='count')
            bike_hour_road = bike_hour_road.sort_values('count', ascending=False).head(10)
            predictions['bicycle_hour_road_risks'] = bike_hour_road.to_dict('records')
            
            # High-risk cantons for cyclists
            bike_canton_severity = bicycle_df.groupby(['CantonCode', 'AccidentSeverityCategory']).size().reset_index(name='count')
            bike_canton_severity = bike_canton_severity.sort_values('count', ascending=False).head(10)
            predictions['bicycle_canton_severity'] = bike_canton_severity.to_dict('records')
    
    # Generate route planning recommendations
    recommendations = []
    
    if 'hour_canton_risks' in predictions and predictions['hour_canton_risks']:
        top_risk = predictions['hour_canton_risks'][0]
        recommendations.append(f"Avoid riding in {top_risk['CantonCode']} around {top_risk['AccidentHour']}:00")
    
    if 'bicycle_hour_road_risks' in predictions and predictions['bicycle_hour_road_risks']:
        top_bike_risk = predictions['bicycle_hour_road_risks'][0]
        recommendations.append(f"High cyclist risk: {top_bike_risk['RoadType_en']} at {top_bike_risk['AccidentHour']}:00")
    
    predictions['recommendations'] = recommendations
    
    return predictions

def calculate_monthly_trends(df, metric_type='total'):
    """
    Calculate monthly trends for sparkline visualization.
    
    Args:
        df (pandas.DataFrame): Accident data
        metric_type (str): Type of metric - 'total', 'fatal', 'bicycle', 'pedestrian'
        
    Returns:
        dict: Monthly counts, current month value, previous month value, and delta
    """
    if df.empty or 'AccidentYear' not in df.columns or 'AccidentMonth' not in df.columns:
        return None
    
    # Filter based on metric type
    if metric_type == 'fatal':
        filtered_df = df[df['AccidentSeverityCategory'] == 'as1']
    elif metric_type == 'bicycle':
        filtered_df = df[df['AccidentInvolvingBicycle'] == 'true']
    elif metric_type == 'pedestrian':
        filtered_df = df[df['AccidentInvolvingPedestrian'] == 'true']
    else:
        filtered_df = df
    
    # Create year-month combination for grouping
    filtered_df = filtered_df.copy()
    filtered_df['year_month'] = filtered_df['AccidentYear'].astype(str) + '-' + filtered_df['AccidentMonth'].astype(str).str.zfill(2)
    
    # Group by year-month
    monthly_counts = filtered_df.groupby('year_month').size().sort_index()
    
    if len(monthly_counts) == 0:
        return None
    
    # Get current and previous month values
    current_month = monthly_counts.iloc[-1]
    previous_month = monthly_counts.iloc[-2] if len(monthly_counts) > 1 else current_month
    
    # Calculate delta
    delta = current_month - previous_month
    delta_pct = (delta / previous_month * 100) if previous_month > 0 else 0
    
    return {
        'monthly_values': monthly_counts.values.tolist(),
        'monthly_labels': monthly_counts.index.tolist(),
        'current_value': int(current_month),
        'previous_value': int(previous_month),
        'delta': int(delta),
        'delta_pct': round(delta_pct, 1)
    }
