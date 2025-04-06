import ee
import webbrowser
import folium
from shapely.geometry import shape
import threading
import os
import tempfile

def add_ee_layer(map_object, ee_image_object, vis_params, name):
    """Adds a method for displaying Earth Engine image tiles to folium map."""
    map_id_dict = ee.Image(ee_image_object).getMapId(vis_params)

    # Print tile URL for debugging
    print(f"Tile URL for {name}: {map_id_dict['tile_fetcher'].url_format}")

    folium.raster_layers.TileLayer(
        tiles=map_id_dict['tile_fetcher'].url_format,
        attr='Map Data &copy; <a href="https://earthengine.google.com/">Google Earth Engine</a>',
        name=name,
        overlay=True,
        control=True
    ).add_to(map_object)

def generate_map(image, geometry, sensor_type):
    """
    Generate an interactive Folium map for Sentinel-2 or Landsat imagery.

    Parameters:
    - image: The Earth Engine image to visualize.
    - geometry: The region of interest (ROI) as a GeoJSON-like dictionary.
    - sensor_type: A string indicating the sensor type ('Sentinel-2' or 'Landsat').
    """
    # Calculate the center of the ROI
    shapely_geom = shape(geometry)
    minx, miny, maxx, maxy = shapely_geom.bounds
    center = [(miny + maxy) / 2, (minx + maxx) / 2]
    lat, lon = center

    # Create Folium map
    m = folium.Map(location=[lat, lon], zoom_start=13)

    # Define visualization parameters
    band_names = image.bandNames().getInfo()  # Get band names from the image

    # Set scale based on sensor type
    scale = 10 if sensor_type == "Sentinel-2" else 30
    
    # Compute min and max dynamically based on the image data
    stats = image.reduceRegion(
        # reducer=ee.Reducer.minMax(),
        reducer=ee.Reducer.percentile([2, 98]),
        geometry=geometry,
        scale=scale,
        bestEffort=True
    ).getInfo()

    # Determine bands dynamically
    if sensor_type == "Sentinel-2":
        bands = ['B4', 'B3', 'B2']
    elif "SR_B6" in band_names and "ST_B10" in band_names:  # Landsat 8/9 Surface Reflectance
        bands = ['SR_B4', 'SR_B3', 'SR_B2']
    elif "SR_B1" in band_names and "ST_B6" in band_names:  # Landsat 7 Surface Reflectance
        bands = ['SR_B3', 'SR_B2', 'SR_B1']
    elif "B10" in band_names and "B11" in band_names:  # Landsat 8/9 TOA
        bands = ['B4', 'B3', 'B2']
    else:  # Landsat 7 TOA
        bands = ['B3', 'B2', 'B1']

    # # Get min and max values for selected bands
    # min_values = [stats.get(band + "_min", 0) for band in bands]
    # max_values = [stats.get(band + "_max", 1) for band in bands]

    # Get percentile min/max values for each band
    min_values = [stats.get(band + "_p2", 0) for band in bands]  # 2nd percentile
    max_values = [stats.get(band + "_p98", 1) for band in bands]  # 98th percentile

    # Set visualization parameters
    vis_params = {'min': min(min_values), 'max': max(max_values), 'bands': bands}

    # Add the image layer
    add_ee_layer(m, image, vis_params, f"{sensor_type} Imagery")

    # Add ROI overlay
    folium.GeoJson(geometry, name="ROI").add_to(m)

    # Add layer control
    m.add_child(folium.LayerControl())

    # Save and open map
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as temp_file:
        temp_path = temp_file.name
    m.save(temp_path)
    webbrowser.open(temp_path)

    def delete_temp_file():
        """Delete the temporary file after closing the browser."""
        import time
        time.sleep(2)
        if os.path.exists(temp_path):
            os.remove(temp_path)
    
    threading.Thread(target=delete_temp_file, daemon=True).start()