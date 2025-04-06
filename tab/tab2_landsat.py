import ee

def authenticate_and_initialize(project):
    """Authenticate and initialize Google Earth Engine."""
    ee.Authenticate()
    ee.Initialize(project=project)
    print("GEE Authentication Successful")

def process_landsat(landsat_version, geometry, start_date, end_date):
    """Process Landsat imagery with cloud reduction using median composite."""
    # Select Landsat collection based on user choice
    landsat_collections = {
        "L9 Surface Reflectance": "LANDSAT/LC09/C02/T1_L2",
        "L9 TOA Reflectance": "LANDSAT/LC09/C02/T1_TOA",
        "L8 Surface Reflectance": "LANDSAT/LC08/C02/T1_L2",
        "L8 TOA Reflectance": "LANDSAT/LC08/C02/T1_TOA",
        "L7 Surface Reflectance": "LANDSAT/LE07/C02/T1_L2",
        "L7 TOA Reflectance": "LANDSAT/LE07/C02/T1_TOA",
    }

    if landsat_version not in landsat_collections:
        print("Invalid Landsat version.")
        return None

    # Filter Landsat collection by date & region
    landsat_collection = (
        ee.ImageCollection(landsat_collections[landsat_version])
        .filterDate(start_date, end_date)
        .filterBounds(geometry)
    )

    # Grab the first image to extract metadata
    first_image = landsat_collection.first()

    # Function to mask clouds using the 'QA_PIXEL' band
    def mask_clouds(image):
        qa_pixel = image.select('QA_PIXEL')
        cloud_mask = qa_pixel.bitwiseAnd(1 << 3).eq(0)  # Cloud mask bit
        return image.updateMask(cloud_mask)

    # Apply cloud masking to each image in the collection
    landsat_collection = landsat_collection.map(mask_clouds)

    # Use median composite to fill gaps
    landsat_composite = landsat_collection.median()

    # Check if an image is available
    if landsat_composite is None:
        print("No valid Landsat images found for the given period and location.")
        return None

    # Function to apply scale factors
    def applyScaleFactors(image):
        opticalBands = image.select('SR_B.*').multiply(0.0000275).add(-0.2)
        thermalBands = image.select('ST_B.*').multiply(0.00341802).add(149.0)
        return image.addBands(opticalBands, None, True).addBands(thermalBands, None, True)

    # Apply scale factors
    if "Surface Reflectance" in landsat_version:
        landsat = applyScaleFactors(landsat_composite)
    else:
        landsat = landsat_composite
    
    # Extract relevant metadata from the first image
    preserved_metadata = ee.Dictionary({
        'SPACECRAFT_ID': first_image.get('SPACECRAFT_ID'),
        'LANDSAT_PRODUCT_ID': first_image.get('LANDSAT_PRODUCT_ID'),
        'system:asset_id': first_image.get('system:asset_id')
    })

    # Set the metadata on the final image before clipping
    landsat = landsat.set(preserved_metadata)

    # Clip the final composite image to the selected geometry
    return landsat.clip(geometry)