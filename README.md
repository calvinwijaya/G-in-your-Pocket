<img src="https://github.com/user-attachments/assets/8471e463-9912-46f7-86d1-ebdcd584e5e5" width="200">

# G-in-your-Pocket: A Simple and Interactive Google Earth Engine GUI for Remote Sensing Analysis
This repository contains code to build and run G-in-your-Pocket. It developed as a simple and interactive GUI designed to streamline access to [Google Earth Engine](https://earthengine.google.com/) functionalities. It features ten tabs covering a comprehensive range of remote sensing tasks, including image import, false color composites, spectral indices, principal component analysis, pansharpening (image fusion), land surface temperature, and both unsupervised and supervised classification.

## Prerequisites & Instalations
The GUI was built in Windows environment, using PyQt6 library. The application communicates with GEE through the Earth Engine API, which is integrated directly into the script. All processing is performed on the backend using GEE, while G-in-your-Pocket functions solely as a front-end interface. To build the application, please follow steps below:
1. Create a conda environment. We use Python 3.9 and not yet test it in another Python version. Activate the environment.
```
conda create --name Gpocket python=3.9
conda activate Gpocket
```
2. Download or clone the code in this Github. Move inside the G-in-your-Pocket in terminal.
3. Install all python packages or library required.
```
pip install requirements.txt
```
List of library used:
```
PyQt6 earthengine-api folium shapely click attrs click-plugins cligj munch six importlib-metadata simplejson PyQt6-WebEngine geemap
```
4. Run the G-in-your-Pocket.
```
python main.py
```
You should now be able to use G-in-your-Pocket. To use G-in-your-Pocket, you need to have a GEE account and register a project.

## How to use
G-in-your-Pocket is developed as a bridge between users and GEE. It offers a simple interface equipped with a complete set of tools for remote sensing processing and analysis. The interface is built with simplicity and interactivity in mind, making it intuitive even for first-time users. The workflow is straightforward and guided. You should know how to use it at first sight, since it is a simple application.

The application consists of ten tabs, each designed for a specific stage of remote sensing analysis. The first two tabs are dedicated to image collection, while the remaining tabs handle processing tasks. As such, users must first collect imagery using either the Sentinel-2 or Landsat options before accessing the subsequent analysis functions. If this step is skipped, the log will notify users that an image must be loaded prior to using other tools.

Some tabs accept only specific input types. For example, the image fusion tab supports only Landsat imagery with TOA Reflectance level, while the LST tab requires Landsat imagery at the Surface Reflectance level. The remaining tabs accept both Sentinel and Landsat imagery at any processing level. Detail function for each tab:

- Tab #1 - Sentinel 2 Imagery Collection

- Tab #2 - Landsat Imagery Collection

- Tab #3 - False Color Composite Visualization

- Tab #4 - Spectral Indices Calculation

- Tab #5 - NDVI Time Series Plot

- Tab #6 - Principal Component Analysis Calculation

- Tab #7 - Pansharpening or Image Fusion

- Tab #8 - Unsupervised Classification

- Tab #9 - Supervised Classification

- Tab #10 - Land Surface Temperature Analysis


## Data
Currently, G-in-your-Pocket support seven types of remote sensing imageries, including:
1. Sentinel 2 Level 2A Surface Reflectance
2. Landsat 9 Surface Reflectance
3.	Landsat 9 TOA Reflectance
4.	Landsat 8 Surface Reflectance
5.	Landsat 8 TOA Reflectance
6.	Landsat 7 Surface Reflectance
7.	Landsat 7 TOA Reflectance

# Citation
The paper of G-in-your-Pocket is still in review process, submitted to [International Conference on Science and Technology (ICST UGM 2025)](https://icst.ugm.ac.id/).
```
@article{,
    Author = {Calvin Wijaya, Ruli Andaru, Dhias Muhammad Naufal},
    Title = {G-in-your-Pocket: A Simple and Interactive Google Earth Engine GUI for Remote Sensing Analysis},
    Conference = {International Conference on Science and Technology (ICST UGM 2025)},
    Year = {2025}
}
```

