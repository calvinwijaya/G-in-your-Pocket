import ee

def get_principal_components(image, region, scale):
    """Computes Principal Components Analysis (PCA) on a given image with selected bands."""

    # Get band names from the image
    band_names = image.bandNames().getInfo()
    print(f"📛 Bands in image: {band_names}")  

    # Define conditions for selecting specific bands
    is_sr = any(b.startswith("SR_") for b in band_names)
    has_st_b10 = "ST_B10" in band_names
    has_b10 = "B10" in band_names
    has_sr_b6 = "SR_B6" in band_names
    has_sr_b1 = "SR_B1" in band_names
    has_st_b6 = "ST_B6" in band_names
    has_b1 = "B1" in band_names
    has_b11 = "B11" in band_names

    is_l8_9_sr = is_sr and has_sr_b6 and has_st_b10
    is_l7_sr = is_sr and has_sr_b1 and has_st_b6 and not has_sr_b6
    is_l8_9_toa = not is_sr and has_b10 and has_b11
    is_l7_toa = not is_sr and not has_b10 and has_b1

    # Select the bands based on conditions
    if is_l8_9_sr:
        selected_bands = ["SR_B5", "SR_B4", "SR_B3", "SR_B2"]
    elif is_l7_sr:
        selected_bands = ["SR_B4", "SR_B3", "SR_B2", "SR_B1"]
    elif is_l8_9_toa:
        selected_bands = ["B5", "B4", "B3", "B2"]
    elif is_l7_toa:
        selected_bands = ["B4", "B3", "B2", "B1"]
    else:
        selected_bands = band_names  # Default to all bands if no condition matches

    print(f"📊 Selected bands for PCA: {selected_bands}")
    image = image.select(selected_bands)

    # Proceed with PCA calculation on selected bands
    band_names = image.bandNames()

    # Compute the mean and subtract it to center the data
    mean_dict = image.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=region,
        scale=scale,
        maxPixels=1e9
    )

    means = ee.Image.constant(mean_dict.values(band_names))
    centered = image.subtract(means)

    # Helper function to generate new band names
    def get_new_band_names(prefix):
        seq = ee.List.sequence(1, band_names.size())
        return seq.map(lambda b: ee.String(prefix).cat(ee.Number(b).int().format()))

    # Convert image to array format
    arrays = centered.toArray()

    # Compute the covariance matrix
    covar = arrays.reduceRegion(
        reducer=ee.Reducer.centeredCovariance(),
        geometry=region,
        scale=scale,
        maxPixels=1e9
    )

    # Extract the covariance matrix as an array
    covar_array = ee.Array(covar.get('array'))

    # Compute the eigenvalues and eigenvectors
    eigens = covar_array.eigen()

    # Extract eigenvalues and eigenvectors
    eigen_values = eigens.slice(1, 0, 1)  # First column (Eigenvalues)
    eigen_vectors = eigens.slice(1, 1)    # Remaining columns (Eigenvectors)

    # Convert input image to array format for matrix multiplication
    array_image = arrays.toArray(1)

    # Perform matrix multiplication to compute principal components
    principal_components = ee.Image(eigen_vectors).matrixMultiply(array_image)

    # Convert eigenvalues into an image for normalization
    sd_image = ee.Image(eigen_values.sqrt()) \
        .arrayProject([0]).arrayFlatten([get_new_band_names('sd')])

    # Normalize the principal components using standard deviation
    pc_image = principal_components \
        .arrayProject([0]) \
        .arrayFlatten([get_new_band_names('pc')]) \
        .divide(sd_image)

    pc_image_band_names = pc_image.bandNames()
    print("PCA Bands:", pc_image_band_names.getInfo())

    return pc_image