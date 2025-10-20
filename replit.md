# Swiss Road Traffic Accidents Dashboard

## Overview

This project is a Streamlit-based interactive dashboard for analyzing and visualizing Swiss road traffic accident data. The application processes GeoJSON accident location data and provides comprehensive insights into traffic safety patterns across Switzerland, with special emphasis on cyclist and pedestrian safety. The dashboard enables users to explore accident trends, identify blackspot zones, perform temporal analysis, and generate risk predictions through an intuitive map-based interface.

## Recent Changes (October 17, 2025)

### Enhanced Features Implemented
1. **Advanced Basemap Integration**: Added multiple basemap options including Swiss Topo, OpenStreetMap (default and variants), Satellite imagery, Terrain maps, and CartoDB with user-selectable basemap styles
2. **Geospatial Clustering**: Implemented DBSCAN clustering algorithm for blackspot zone identification with configurable distance thresholds and minimum accident counts
3. **Cyclist Safety Dashboard**: Created dedicated tab with bicycle-specific metrics, risk patterns, temporal analysis, blackspot visualization, and safety recommendations
4. **Time-Series Enhancements**: Added seasonal pattern analysis using Fourier analysis and year-over-year trend comparisons with statistical visualizations
5. **Predictive Analytics**: Implemented risk prediction system showing high-risk time/location combinations for route planning with cyclist-specific recommendations
6. **Data Export**: Enhanced export capabilities with CSV download and built-in Plotly chart export functionality

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
**Problem**: Need to provide interactive data visualization and analysis capabilities for Swiss traffic accident data.

**Solution**: Streamlit framework for rapid development of data-driven web applications.

**Key Components**:
- **Main Application** (`app.py`): Orchestrates the dashboard UI, handles user interactions through sidebar filters, and coordinates data flow between modules
- **Interactive Maps**: Uses Folium with Streamlit integration (`streamlit_folium`) for geospatial visualizations
- **Data Visualizations**: Plotly library for interactive charts, graphs, and statistical displays
- **Wide Layout**: Configured for optimal data visualization with expandable sidebar for filtering controls

**Rationale**: Streamlit's declarative approach allows rapid development of interactive dashboards without frontend framework complexity. The combination with Folium and Plotly provides rich geospatial and statistical visualization capabilities.

### Data Processing Architecture
**Problem**: Need to process GeoJSON geographic data into analyzable formats and perform complex analytics.

**Solution**: Pandas-based ETL pipeline with specialized analytics modules.

**Key Components**:
- **Data Loader** (`data_loader.py`): Extracts features from GeoJSON, transforms coordinates and properties into structured DataFrame format
- **Analytics Engine** (`analytics.py`): Implements statistical analysis including summary statistics, temporal analysis, clustering algorithms (DBSCAN), and risk predictions using scipy and sklearn
- **Caching Strategy**: Streamlit's `@st.cache_data` decorator for performance optimization

**Design Decisions**:
- GeoJSON coordinate extraction with longitude/latitude normalization
- Multi-language support (German, French, Italian, English) preserved in data structure
- Statistical computations using numpy and scipy for performance
- DBSCAN clustering for blackspot identification

### Map Visualization System
**Problem**: Need flexible, interactive map visualizations with multiple basemap options and overlay capabilities.

**Solution**: Folium-based mapping system with plugin support.

**Key Components** (`map_utils.py`):
- **Base Map Creation**: Configurable basemap styles including OpenStreetMap, Swiss Topo, Satellite, Terrain, and CartoDB
- **Marker System**: Accident location visualization with customizable markers
- **Heatmap Layer**: HeatMap plugin for density visualization
- **Blackspot Mapping**: Specialized visualization for high-risk zones

**Technical Choices**:
- Swiss Topo integration for local accuracy (WMTS service)
- Multiple basemap providers for different analysis contexts
- Plugin architecture (HeatMap) for advanced visualizations
- Switzerland-centered default view (46.8182, 8.2275) with appropriate zoom level

### Analytics Capabilities
**Problem**: Need comprehensive analytical features for accident pattern identification and risk assessment.

**Solution**: Modular analytics functions leveraging scientific Python stack.

**Implemented Analyses**:
- **Summary Statistics**: Accident counts, severity distribution, involved party analysis (bicycle, pedestrian, motorcycle percentages)
- **Temporal Analysis**: Year-over-year trends, seasonal patterns, hourly distributions
- **Spatial Analysis**: Blackspot zone identification using DBSCAN clustering, geographic risk assessment
- **Filtering System**: Multi-dimensional filtering by year, canton, severity, accident type, and involved parties
- **Predictive Analytics**: Risk prediction capabilities using historical patterns

**Libraries Used**:
- Pandas/Numpy: Data manipulation and numerical computations
- Scipy: Spatial distance calculations for clustering
- Scikit-learn: DBSCAN clustering algorithm for blackspot detection

### Data Schema
**Structure**: GeoJSON FeatureCollection with Point geometries and rich property metadata.

**Key Fields**:
- Unique identifiers (AccidentUID)
- Accident classification (Type, Severity)
- Involved parties (Pedestrian, Bicycle, Motorcycle flags)
- Location data (Swiss coordinates CHLV95, canton, municipality)
- Temporal data (Year, Month, WeekDay, Hour)
- Multi-language descriptive fields (de/fr/it/en)
- Road characteristics (RoadType)

## External Dependencies

### Core Framework Dependencies
- **Streamlit**: Web application framework for dashboard interface
- **streamlit-folium**: Bridge library for embedding Folium maps in Streamlit

### Data Processing Libraries
- **Pandas**: Primary data manipulation and DataFrame operations
- **NumPy**: Numerical computations and array operations
- **JSON**: GeoJSON data parsing (Python standard library)

### Visualization Libraries
- **Folium**: Interactive map generation and geospatial visualization
- **folium.plugins.HeatMap**: Heatmap overlay functionality
- **Plotly Express & Graph Objects**: Interactive charts and statistical plots
- **Plotly Subplots**: Multi-panel visualization layouts

### Scientific Computing
- **Scipy (scipy.spatial)**: Spatial distance calculations for clustering analysis
- **Scikit-learn (sklearn.cluster.DBSCAN)**: Density-based clustering for blackspot identification

### Data Source
- **Swiss Road Traffic Accident Data**: GeoJSON format files containing accident location and attribute data
- **Swiss Topo WMTS Service**: Swiss topographic basemap tiles (https://wmts.geo.admin.ch)
- **ArcGIS Online**: Satellite and terrain basemap services
- **CartoDB**: Alternative basemap provider

### File System
- Local JSON file storage for accident data (`attached_assets/` directory)
- GeoJSON format for geographic features
- Schema definition files for data structure documentation