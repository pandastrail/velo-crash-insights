# Swiss Road Traffic ~~Accidents~~ Crahses Dashboard

## Overview

This project is a Streamlit-based interactive dashboard for analyzing and visualizing Swiss road traffic accident data. The application processes GeoJSON accident location data and provides comprehensive insights into traffic safety patterns across Switzerland, with special emphasis on cyclist and pedestrian safety. The dashboard enables users to explore accident trends, identify blackspot zones, perform temporal analysis, and generate risk predictions through an intuitive map-based interface.

> This data app has been created while participating at the [2025 Cycling HACK event in Zürich](https://cyclinghack.ch/events/zurich-2025/)

## Quickstart

### 1. Create and activate a virtual environment

Run the commands from the repository root.

```powershell
python -m venv .venv
.\.venv\Scripts\activate
```

```bash
python -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Provide the dataset

- Place the full GeoJSON export in `attached_assets/RoadTrafficAccidentLocations.json`. The app expects that exact filename and folder. Data available at [opendata.swiss](https://opendata.swiss/en/dataset/polizeilich-registrierte-verkehrsunfalle-auf-dem-stadtgebiet-zurich-seit-2011).
- A trimmed sample (`RoadTrafficAccidentLocations_sample_*.json`) is included for quick tests, but the full dashboard experience requires the complete dataset.

### 4. Run the Streamlit app

```bash
streamlit run app.py
```

Streamlit starts a local server (default `http://localhost:8501`) and opens the dashboard in your browser.

## Features Implemented

1. **Geospatial Clustering**: Implemented DBSCAN clustering algorithm for blackspot zone identification with configurable distance thresholds and minimum accident counts
2. **Cyclist Safety Dashboard**: Created dedicated tab with bicycle-specific metrics, risk patterns, temporal analysis, blackspot visualization, and safety recommendations
3. **Time-Series Enhancements**: Added seasonal pattern analysis using Fourier analysis and year-over-year trend comparisons with statistical visualizations
4. **Predictive Analytics**: Implemented risk prediction system showing high-risk time/location combinations for route planning with cyclist-specific recommendations
5. **Data Export**: Enhanced export capabilities with CSV download and built-in Plotly chart export functionality

## Featured added but not tested

1. **Advanced Basemap Integration**: Added multiple basemap options including Swiss Topo, OpenStreetMap (default and variants), Satellite imagery, Terrain maps, and CartoDB with user-selectable basemap styles

## Ideas for further development

- **Add docs, definitions, glossary**: Semantics from opendata.swiss dataset schema
- **Add exact location**: street, plz, city, etc., to blackspots/hotspots and tables (use Swiss Geo API to derive location).
- **Data Enrichment**: Add historical weather data to each record, like temperature, rainfall, icing, fog etc. and explore correlations. Add other external factors, for example, covid-period, mass events, rider charaterization (age, skill level, etc.), equipment attributes (bike type, gear, etc.), car traffic volume, construction sites, others?
- **Add Regions or Clusters**: To define risk areas and group dimensions.
- **Smart routing capabilities**: Considering crash data, day of week, time of day, etc. Connectors to Garmin, Strava, Google Maps, others?
- **Native App**: Create a simplified Native App (iOS and Android) with live predictors on my route.
- What else?

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

- **Data Loader** (`data_loader.py`): Extracts features
from GeoJSON, transforms coordinates and properties into structured DataFrame format
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
- **Swiss Topo WMTS Service**: Swiss topographic basemap tiles [WMTS](https://wmts.geo.admin.ch)
- **ArcGIS Online**: Satellite and terrain basemap services
- **CartoDB**: Alternative basemap provider

### File System

- Local JSON file storage for accident data (`attached_assets/` directory)
- GeoJSON format for geographic features
- Schema definition files for data structure documentation
