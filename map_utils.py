import folium
from folium.plugins import HeatMap, LocateControl, Fullscreen, Draw, MiniMap, MousePosition, MeasureControl
import pandas as pd
import numpy as np

def create_base_map(basemap_style='OpenStreetMap'):
    """
    Create a base map centered on Switzerland with selectable basemap styles.
    
    Args:
        basemap_style (str): Basemap style to use
        
    Returns:
        folium.Map: Base map object
    """
    # Switzerland center coordinates
    switzerland_center = [46.8182, 8.2275]
    
    # Define basemap options
    basemap_tiles = {
        'OpenStreetMap': 'OpenStreetMap',
        'Swiss Topo': 'https://wmts.geo.admin.ch/1.0.0/ch.swisstopo.pixelkarte-farbe/default/current/3857/{z}/{x}/{y}.jpeg',
        'Satellite': 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        'Terrain': 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Terrain_Base/MapServer/tile/{z}/{y}/{x}',
        'CartoDB': 'CartoDB positron'
    }
    
    # Create map with selected basemap
    if basemap_style in basemap_tiles:
        tile_url = basemap_tiles[basemap_style]
        if basemap_style == 'Swiss Topo':
            m = folium.Map(
                location=switzerland_center,
                zoom_start=8,
                tiles=tile_url,
                attr='© swisstopo',
                scrollWheelZoom=True,
                options={'wheelPxPerZoomLevel': 120}
            )
        elif basemap_style in ['Satellite', 'Terrain']:
            m = folium.Map(
                location=switzerland_center,
                zoom_start=8,
                tiles=tile_url,
                attr='Esri',
                scrollWheelZoom=True,
                options={'wheelPxPerZoomLevel': 120}
            )
        else:
            m = folium.Map(
                location=switzerland_center,
                zoom_start=8,
                tiles=tile_url,
                scrollWheelZoom=True,
                options={'wheelPxPerZoomLevel': 120}
            )
    else:
        m = folium.Map(
            location=switzerland_center,
            zoom_start=8,
            tiles='OpenStreetMap',
            scrollWheelZoom=True,
            options={'wheelPxPerZoomLevel': 120}
        )
    
    # Add alternative basemap layers
    for name, tile in basemap_tiles.items():
        if name != basemap_style:
            if name == 'Swiss Topo':
                folium.TileLayer(
                    tiles=tile,
                    attr='© swisstopo',
                    name=name,
                    overlay=False,
                    control=True
                ).add_to(m)
            elif name in ['Satellite', 'Terrain']:
                folium.TileLayer(
                    tiles=tile,
                    attr='Esri',
                    name=name,
                    overlay=False,
                    control=True
                ).add_to(m)
            else:
                folium.TileLayer(
                    tiles=tile,
                    name=name,
                    overlay=False,
                    control=True
                ).add_to(m)
    
    # Add "My Location" button
    LocateControl(
        auto_start=False,
        position='topleft',
        strings={'title': 'Show my location', 'popup': 'You are here'}
    ).add_to(m)
    
    # Add fullscreen button
    Fullscreen(
        position='topleft',
        title='Enter fullscreen mode',
        title_cancel='Exit fullscreen mode',
        force_separate_button=True
    ).add_to(m)
    
    # Add MiniMap (overview map in corner)
    MiniMap(
        toggle_display=True,
        tile_layer='OpenStreetMap',
        position='bottomright',
        width=150,
        height=150,
        zoom_level_offset=-5
    ).add_to(m)
    
    # Add Mouse Position (shows coordinates on hover)
    MousePosition(
        position='bottomleft',
        separator=' | ',
        prefix='Coordinates:',
        lat_formatter="function(num) {return L.Util.formatNum(num, 5) + ' N';}",
        lng_formatter="function(num) {return L.Util.formatNum(num, 5) + ' E';}"
    ).add_to(m)
    
    # Add Measure Control (measure distances and areas)
    MeasureControl(
        position='topleft',
        primary_length_unit='kilometers',
        secondary_length_unit='meters',
        primary_area_unit='sqkilometers',
        secondary_area_unit='sqmeters'
    ).add_to(m)
    
    # Add Draw tools (allows drawing shapes, markers, etc.)
    Draw(
        export=True,
        position='topleft',
        draw_options={
            'polyline': {'shapeOptions': {'color': '#f06eaa'}},
            'polygon': {'shapeOptions': {'color': '#6bc2e5'}},
            'circle': True,
            'rectangle': {'shapeOptions': {'color': '#662d91'}},
            'marker': True,
            'circlemarker': False
        },
        edit_options={'edit': True}
    ).add_to(m)
    
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
        'as3': 'yellow',   # Light injuries
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
        df = df.sample(n=max_markers)
    
    # Group markers by type for different layers
    severity_groups = df.groupby('AccidentSeverityCategory')
    
    for severity, group in severity_groups:
        feature_group = folium.FeatureGroup(name=f"Severity: {severity}")
        
        for idx, row in group.iterrows():
            try:
                # Create popup content
                popup_html = f"""
                <div style="width: 200px;">
                    <b>Accident Details</b><br>
                    <b>Type:</b> {row.get('AccidentType_en', 'Unknown')}<br>
                    <b>Severity:</b> {row.get('AccidentSeverityCategory_en', 'Unknown')}<br>
                    <b>Road:</b> {row.get('RoadType_en', 'Unknown')}<br>
                    <b>Date:</b> {row.get('AccidentYear', 'N/A')}-{row.get('AccidentMonth', 'N/A')}<br>
                    <b>Time:</b> {row.get('AccidentHour_text', 'Unknown')}<br>
                    <b>Canton:</b> {row.get('CantonCode', 'Unknown')}<br>
                    <b>Bicycle:</b> {'Yes' if row.get('AccidentInvolvingBicycle') == 'true' else 'No'}<br>
                    <b>Pedestrian:</b> {'Yes' if row.get('AccidentInvolvingPedestrian') == 'true' else 'No'}<br>
                    <b>Motorcycle:</b> {'Yes' if row.get('AccidentInvolvingMotorcycle') == 'true' else 'No'}
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
                    tooltip=f"{row.get('AccidentType_en', 'Unknown')} - {row.get('CantonCode', 'Unknown')}"
                ).add_to(feature_group)
                
            except Exception as e:
                # Skip problematic markers
                continue
        
        feature_group.add_to(m)
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
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

def add_geocoding_search(m):
    """
    Add geocoding search control to find locations by name.
    
    Args:
        m (folium.Map): Map object
        
    Returns:
        folium.Map: Map with search control added
    """
    # Add Leaflet Geocoder via custom HTML/JS
    geocoder_script = """
    <link rel="stylesheet" href="https://unpkg.com/leaflet-control-geocoder/dist/Control.Geocoder.css" />
    <script src="https://unpkg.com/leaflet-control-geocoder/dist/Control.Geocoder.js"></script>
    <script>
        setTimeout(function() {
            var map = window.map_object;
            if (map) {
                L.Control.geocoder({
                    defaultMarkGeocode: false,
                    position: 'topright',
                    placeholder: 'Search for location...',
                    errorMessage: 'Location not found'
                })
                .on('markgeocode', function(e) {
                    var bbox = e.geocode.bbox;
                    var poly = L.polygon([
                        bbox.getSouthEast(),
                        bbox.getNorthEast(),
                        bbox.getNorthWest(),
                        bbox.getSouthWest()
                    ]);
                    map.fitBounds(poly.getBounds());
                    
                    L.marker(e.geocode.center)
                        .addTo(map)
                        .bindPopup(e.geocode.name)
                        .openPopup();
                })
                .addTo(map);
            }
        }, 1000);
    </script>
    """
    
    m.get_root().html.add_child(folium.Element(geocoder_script))
    
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
