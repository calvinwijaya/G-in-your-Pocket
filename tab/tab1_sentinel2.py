import ee

def authenticate_and_initialize(project):
    """Authenticate and initialize Google Earth Engine."""
    ee.Authenticate()
    ee.Initialize(project=project)
    print("GEE Authentication Successful")

def process_sentinel2(geometry, start_date, end_date, max_cloud_prob):
    """Process Sentinel-2 imagery with cloud masking."""
    s2_sr = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
    s2_clouds = ee.ImageCollection("COPERNICUS/S2_CLOUD_PROBABILITY")

    def mask_clouds(img):
        clouds = ee.Image(img.get("cloud_mask")).select("probability")
        is_not_cloud = clouds.lt(max_cloud_prob)
        return img.updateMask(is_not_cloud)

    criteria = ee.Filter.bounds(geometry).And(ee.Filter.date(start_date, end_date))
    s2_sr_filtered = s2_sr.filter(criteria)
    s2_clouds_filtered = s2_clouds.filter(criteria)

    join = ee.Join.saveFirst("cloud_mask")
    condition = ee.Filter.equals(leftField="system:index", rightField="system:index")
    s2_sr_with_cloud_mask = join.apply(s2_sr_filtered, s2_clouds_filtered, condition)

    s2_cloud_masked = ee.ImageCollection(s2_sr_with_cloud_mask).map(mask_clouds).median()
    return s2_cloud_masked.clip(geometry)
