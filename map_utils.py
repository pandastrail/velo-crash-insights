import folium
from folium.plugins import HeatMap, LocateControl, Fullscreen, Draw, MiniMap, MousePosition, MeasureControl, Geocoder
import pandas as pd
import numpy as np

# --- Minimal base map: OSM + CyclOSM, zoom, my-location, fullscreen ---
import folium
from folium.plugins import HeatMap, LocateControl, Fullscreen

def create_base_map(basemap_style='OpenStreetMap'):
    # Center on Switzerland; zoom gets overridden by fit_map_to_df
    m = folium.Map(location=[47.38, 8.55], zoom_start=13, tiles='OpenStreetMap',
                   scrollWheelZoom=False, options={'wheelPxPerZoomLevel': 120})

    # CyclOSM overlay (always on; no layer control)
    folium.TileLayer(
        tiles='https://{s}.tile-cyclosm.openstreetmap.fr/cyclosm/{z}/{x}/{y}.png',
        attr='CyclOSM | © OpenStreetMap contributors',
        name='Cycling Routes',
        overlay=True,
        control=False,
        opacity=0.9
    ).add_to(m)

    # My location + fullscreen (Leaflet’s zoom control is on by default)
    LocateControl(auto_start=False, position='topleft').add_to(m)
    Fullscreen(position='topleft', force_separate_button=True).add_to(m)
    return m


def get_marker_color(severity):
    """
    Get marker color based on accident severity.
    
    Args:
        severity (str): Accident severity category
        
    Returns:
        str: Color name for marker
    """
    color_map = {
        'as1': 'red',      # Fatal
        'as2': 'orange',   # Severe injuries
        'as3': 'lightgreen',   # Light injuries
        'as4': 'green'     # Property damage only
    }
    
    return color_map.get(severity, 'blue')

def get_severity_icon(severity):
    """
    Get appropriate icon based on severity.
    
    Args:
        severity (str): Accident severity category
        
    Returns:
        str: Icon name
    """
    icon_map = {
        'as1': 'exclamation-triangle',  # Fatal
        'as2': 'exclamation-circle',    # Severe injuries
        'as3': 'info-circle',           # Light injuries
        'as4': 'circle'                 # Property damage only
    }
    
    return icon_map.get(severity, 'circle')

def add_accident_markers(m, df, max_markers=500):
    """
    Add accident markers to the map.
    
    Args:
        m (folium.Map): Map object
        df (pandas.DataFrame): Accident data
        max_markers (int): Maximum number of markers to display
        
    Returns:
        folium.Map: Map with markers added
    """
    if df.empty:
        return m
    
    # Limit markers for performance
    if len(df) > max_markers:
        df = df.sample(n=max_markers, random_state=42)
    
    # Group markers by type for different layers
    severity_groups = df.groupby('AccidentSeverityCategory')
    
    for severity, group in severity_groups:
        feature_group = folium.FeatureGroup(name=f"Severity: {severity}")
        
        for idx, row in group.iterrows():
            try:
                # Create popup content
                popup_html = f"""
                    <div style="width: 250px; font-size: 13px; line-height: 1.3;">
                    <h4 style="margin-bottom:4px; color:#d9534f;">🚦 {row.get('AccidentType_en', 'Unknown')}</h4>
                    <b>Severity:</b> {row.get('AccidentSeverityCategory_en', 'Unknown')}<br>
                    <b>Road type:</b> {row.get('RoadType_en', 'Unknown')}<br>
                    <b>Weather:</b> {row.get('WeatherCondition_en', 'Unknown')}<br>
                    <b>Lighting:</b> {row.get('LightCondition_en', 'Unknown')}<br>
                    <hr style="margin:4px 0;">
                    <b>Date:</b> {row.get('AccidentYear', 'N/A')}-{row.get('AccidentMonth', 'N/A'):02d} at {row.get('AccidentHour_text', 'Unknown')}<br>
                    <b>Canton:</b> {row.get('CantonCode', 'Unknown')}<br>
                    <b>Municipality:</b> {row.get('MunicipalityName', 'Unknown')}<br>
                    <hr style="margin:4px 0;">
                    <b>Parties involved:</b><br>
                    🚲 Bicycle: {'✅' if str(row.get('AccidentInvolvingBicycle')).lower() == 'true' else '❌'}<br>
                    🚶 Pedestrian: {'✅' if str(row.get('AccidentInvolvingPedestrian')).lower() == 'true' else '❌'}<br>
                    🏍️ Motorcycle: {'✅' if str(row.get('AccidentInvolvingMotorcycle')).lower() == 'true' else '❌'}<br>
                    </div>
                    """
                # Determine marker style based on involved parties
                if row.get('AccidentInvolvingBicycle') == 'true':
                    icon = 'bicycle'
                    prefix = 'fa'
                elif row.get('AccidentInvolvingPedestrian') == 'true':
                    icon = 'walking'
                    prefix = 'fa'
                elif row.get('AccidentInvolvingMotorcycle') == 'true':
                    icon = 'motorcycle'
                    prefix = 'fa'
                else:
                    icon = get_severity_icon(severity)
                    prefix = 'glyphicon'
                
                # Create marker
                folium.Marker(
                    location=[row['latitude'], row['longitude']],
                    popup=folium.Popup(popup_html, max_width=250),
                    icon=folium.Icon(
                        color=get_marker_color(severity),
                        icon=icon,
                        prefix=prefix
                    ),
                    tooltip=f"{row.get('AccidentType_en', 'Unknown')} • {row.get('AccidentSeverityCategory_en', 'Unknown')} • {row.get('AccidentYear', '')}"
                ).add_to(feature_group)
                
            except Exception as e:
                # Skip problematic markers
                continue
        
        feature_group.add_to(m)
    
    return m

def create_heatmap(df, basemap_style='OpenStreetMap'):
    """
    Create a heatmap of accident locations.
    
    Args:
        df (pandas.DataFrame): Accident data
        basemap_style (str): Basemap style to use
        
    Returns:
        folium.Map: Map with heatmap
    """
    m = create_base_map(basemap_style)
    
    if df.empty:
        return m
    
    # Prepare data for heatmap
    heat_data = []
    for idx, row in df.iterrows():
        try:
            lat = float(row['latitude'])
            lon = float(row['longitude'])
            
            # Weight by severity (higher weight for more severe accidents)
            weight = 1
            if row.get('AccidentSeverityCategory') == 'as1':  # Fatal
                weight = 5
            elif row.get('AccidentSeverityCategory') == 'as2':  # Severe
                weight = 3
            elif row.get('AccidentSeverityCategory') == 'as3':  # Light
                weight = 1
            
            heat_data.append([lat, lon, weight])
        except (ValueError, TypeError):
            continue
    
    if heat_data:
        # Create heatmap
        HeatMap(
            heat_data,
            min_opacity=0.3,
            radius=15,
            blur=10,
            max_zoom=1,
        ).add_to(m)
    
    return m

def create_clustered_map(df):
    """
    Create a map with clustered markers for better performance with large datasets.
    
    Args:
        df (pandas.DataFrame): Accident data
        
    Returns:
        folium.Map: Map with clustered markers
    """
    from folium.plugins import MarkerCluster
    
    m = create_base_map()
    
    if df.empty:
        return m
    
    # Create marker cluster
    marker_cluster = MarkerCluster().add_to(m)
    
    for idx, row in df.iterrows():
        try:
            popup_html = f"""
            <b>{row.get('AccidentType_en', 'Unknown')}</b><br>
            Severity: {row.get('AccidentSeverityCategory_en', 'Unknown')}<br>
            Canton: {row.get('CantonCode', 'Unknown')}<br>
            Year: {row.get('AccidentYear', 'N/A')}
            """
            
            folium.Marker(
                location=[row['latitude'], row['longitude']],
                popup=popup_html,
                icon=folium.Icon(
                    color=get_marker_color(row.get('AccidentSeverityCategory', 'unknown')),
                    icon='info-sign'
                )
            ).add_to(marker_cluster)
            
        except Exception:
            continue
    
    return m

def create_blackspot_map(blackspots_df, basemap_style='Swiss Topo'):
    """
    Create a map showing accident blackspot zones.
    
    Args:
        blackspots_df (pandas.DataFrame): Blackspot data with cluster information
        basemap_style (str): Basemap style to use
        
    Returns:
        folium.Map: Map with blackspot markers
    """
    m = create_base_map(basemap_style)
    
    if blackspots_df.empty:
        return m
    
    # Add circle markers for each blackspot
    for idx, spot in blackspots_df.iterrows():
        # Determine color based on risk score
        if spot['risk_score'] >= 50:
            color = 'red'
            fill_color = 'red'
        elif spot['risk_score'] >= 20:
            color = 'orange'
            fill_color = 'orange'
        else:
            color = 'yellow'
            fill_color = 'yellow'
        
        # Create popup content
        popup_html = f"""
        <div style="width: 250px;">
            <b style="color: {color};">⚠️ Accident Blackspot Zone</b><br>
            <hr>
            <b>Total Accidents:</b> {spot['accident_count']}<br>
            <b>Fatal:</b> {spot['fatal_accidents']} | 
            <b>Severe:</b> {spot['severe_accidents']} | 
            <b>Light:</b> {spot['light_accidents']}<br>
            <b>Bicycle Involved:</b> {spot['bicycle_accidents']}<br>
            <b>Canton:</b> {spot['canton']}<br>
            <b>Common Type:</b> {spot['most_common_type']}<br>
            <b>Risk Score:</b> {spot['risk_score']}
        </div>
        """
        
        # Add circle marker
        folium.CircleMarker(
            location=[spot['center_lat'], spot['center_lon']],
            radius=min(spot['accident_count'] * 2, 30),
            popup=folium.Popup(popup_html, max_width=300),
            color=color,
            fill=True,
            fill_color=fill_color,
            fill_opacity=0.6,
            weight=2,
            tooltip=f"Blackspot: {spot['accident_count']} accidents"
        ).add_to(m)
    
    return m
def add_routing_control(m):
    """
    Add routing control to the map using Leaflet Routing Machine.
    Note: This requires internet connection to use OSRM routing service.
    
    Args:
        m (folium.Map): Map object
        
    Returns:
        folium.Map: Map with routing control added
    """
    # Add Leaflet Routing Machine via custom HTML/JS
    routing_script = """
    <link rel="stylesheet" href="https://unpkg.com/leaflet-routing-machine@latest/dist/leaflet-routing-machine.css" />
    <script src="https://unpkg.com/leaflet-routing-machine@latest/dist/leaflet-routing-machine.js"></script>
    <script>
        // Wait for map to be ready
        setTimeout(function() {
            var map = window.map_object;
            if (map) {
                L.Routing.control({
                    waypoints: [],
                    routeWhileDragging: true,
                    geocoder: L.Control.Geocoder.nominatim(),
                    router: L.Routing.osrmv1({
                        serviceUrl: 'https://router.project-osrm.org/route/v1'
                    }),
                    lineOptions: {
                        styles: [{color: '#6FA1EC', weight: 4, opacity: 0.7}]
                    },
                    show: true,
                    addWaypoints: true,
                    draggableWaypoints: true,
                    fitSelectedRoutes: true,
                    showAlternatives: true,
                    position: 'topright'
                }).addTo(map);
            }
        }, 1000);
    </script>
    """
    
    m.get_root().html.add_child(folium.Element(routing_script))
    
    return m

def add_custom_osm_layers(m):
    """
    Add additional OpenStreetMap-based layers (cycling routes, hiking trails, etc.).
    
    Args:
        m (folium.Map): Map object
        
    Returns:
        folium.Map: Map with additional OSM layers
    """
    # Add OpenStreetMap Cycle Map layer
    folium.TileLayer(
        tiles='https://{s}.tile-cyclosm.openstreetmap.fr/cyclosm/{z}/{x}/{y}.png',
        attr='CyclOSM | Map data: © OpenStreetMap contributors',
        name='Cycling Routes',
        overlay=True,
        control=True,
        opacity=0.7
    ).add_to(m)
    
    # Add OpenTopoMap layer
    folium.TileLayer(
        tiles='https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
        attr='Map data: © OpenStreetMap contributors, SRTM | Map style: © OpenTopoMap',
        name='Topographic',
        overlay=False,
        control=True
    ).add_to(m)
    
    # Add Humanitarian OSM layer
    folium.TileLayer(
        tiles='https://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png',
        attr='© OpenStreetMap contributors, Tiles courtesy of Humanitarian OpenStreetMap Team',
        name='Humanitarian',
        overlay=False,
        control=True
    ).add_to(m)
    
    return m

# --- add near other helpers ---
def fit_map_to_df(m, df, lat_col="Latitude", lon_col="Longitude", pad_deg=0.01):
    """Fit Folium map to the bounding box of points. Handles 0 or 1 point gracefully."""
    if df is None or df.empty or lat_col not in df or lon_col not in df:
        return m

    lats = df[lat_col].astype(float)
    lons = df[lon_col].astype(float)
    lat_min, lat_max = lats.min(), lats.max()
    lon_min, lon_max = lons.min(), lons.max()

    if lat_min == lat_max and lon_min == lon_max:
        m.location = [lat_min, lon_min]
        m.zoom_start = 12
        return m

    lat_min -= pad_deg; lat_max += pad_deg
    lon_min -= pad_deg; lon_max += pad_deg

    # Fit bounds and set an approximate center (to help Streamlit)
    bounds = [[lat_min, lon_min], [lat_max, lon_max]]
    m.fit_bounds(bounds)
    m.location = [(lat_min + lat_max) / 2, (lon_min + lon_max) / 2]
    m.zoom_start = 11  # override CH default
    return m

def add_geocoding_search(m):
    """Add a visible geocoder search box (works with st_folium)."""
    Geocoder(
        add_marker=True,          # drop a marker on result
        collapsed=False,          # show the search box by default
        position='topright',      # matches your UI
        placeholder='Search for location',
        zoom=14
    ).add_to(m)
    return m
