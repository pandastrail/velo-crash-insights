import json
import pandas as pd
import streamlit as st
from replit.object_storage import Client

def load_accident_data(file_path, use_object_storage=False):
    """
    Load and process the GeoJSON accident data.
    
    Args:
        file_path (str): Path to the GeoJSON file (local or object name in bucket)
        use_object_storage (bool): Whether to load from Object Storage
        
    Returns:
        pandas.DataFrame: Processed accident data
    """
    try:
        # Load GeoJSON data
        if use_object_storage:
            client = Client()
            geojson_text = client.download_as_text(file_path)
            geojson_data = json.loads(geojson_text)
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                geojson_data = json.load(f)
        
        # Extract features
        features = geojson_data.get('features', [])
        
        if not features:
            st.error("No features found in the GeoJSON file.")
            return pd.DataFrame()
        
        # Convert to DataFrame
        rows = []
        for feature in features:
            # Extract geometry
            geometry = feature.get('geometry', {})
            coordinates = geometry.get('coordinates', [])
            
            if len(coordinates) >= 2:
                longitude = coordinates[0]
                latitude = coordinates[1]
            else:
                continue  # Skip features without proper coordinates
            
            # Extract properties
            properties = feature.get('properties', {})
            
            # Create row with coordinates and properties
            row = {
                'longitude': longitude,
                'latitude': latitude,
                **properties
            }
            rows.append(row)
        
        if not rows:
            st.error("No valid accident records found in the data.")
            return pd.DataFrame()
        
        # Create DataFrame
        df = pd.DataFrame(rows)
        
        # Data cleaning and type conversion
        # Convert string years to integers for proper sorting
        if 'AccidentYear' in df.columns:
            df['AccidentYear'] = pd.to_numeric(df['AccidentYear'], errors='coerce')
        
        # Convert month to integer
        if 'AccidentMonth' in df.columns:
            df['AccidentMonth'] = pd.to_numeric(df['AccidentMonth'], errors='coerce')
        
        # Convert hour to integer
        if 'AccidentHour' in df.columns:
            df['AccidentHour'] = pd.to_numeric(df['AccidentHour'], errors='coerce')
        
        # Handle missing values
        df = df.dropna(subset=['longitude', 'latitude'])
        
        # Validate coordinate ranges for Switzerland
        # Switzerland approximate bounds: lat 45.8-47.8, lon 5.9-10.5
        df = df[
            (df['latitude'].between(45.0, 48.0)) & 
            (df['longitude'].between(5.0, 11.0))
        ]
        
        if df.empty:
            st.error("No valid accidents found within Switzerland's boundaries.")
            return pd.DataFrame()
        
        st.success(f"Successfully loaded {len(df)} accident records")
        return df
        
    except FileNotFoundError:
        st.error(f"Data file not found: {file_path}")
        return pd.DataFrame()
    except json.JSONDecodeError as e:
        st.error(f"Error parsing JSON data: {str(e)}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Unexpected error loading data: {str(e)}")
        return pd.DataFrame()

def get_data_summary(df):
    """
    Generate a summary of the accident data.
    
    Args:
        df (pandas.DataFrame): Accident data
        
    Returns:
        dict: Summary statistics
    """
    if df.empty:
        return {}
    
    summary = {
        'total_accidents': len(df),
        'date_range': {
            'start': df['AccidentYear'].min() if 'AccidentYear' in df.columns else None,
            'end': df['AccidentYear'].max() if 'AccidentYear' in df.columns else None
        },
        'cantons': df['CantonCode'].nunique() if 'CantonCode' in df.columns else 0,
        'accident_types': df['AccidentType'].nunique() if 'AccidentType' in df.columns else 0,
        'severity_distribution': df['AccidentSeverityCategory_en'].value_counts().to_dict() if 'AccidentSeverityCategory_en' in df.columns else {},
        'involving_bicycle': len(df[df['AccidentInvolvingBicycle'] == 'true']) if 'AccidentInvolvingBicycle' in df.columns else 0,
        'involving_pedestrian': len(df[df['AccidentInvolvingPedestrian'] == 'true']) if 'AccidentInvolvingPedestrian' in df.columns else 0,
        'involving_motorcycle': len(df[df['AccidentInvolvingMotorcycle'] == 'true']) if 'AccidentInvolvingMotorcycle' in df.columns else 0
    }
    
    return summary
