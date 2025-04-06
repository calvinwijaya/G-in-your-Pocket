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
<img src="https://github.com/user-attachments/assets/a7c15cc7-02e6-4a96-9249-10277ba545ed" width="600">

- Tab #2 - Landsat Imagery Collection
<img src="https://github.com/user-attachments/assets/c47ac8bd-cf92-4305-bc39-d70d7f71e257" width="600">

- Tab #3 - False Color Composite Visualization
<img src="https://github.com/user-attachments/assets/f664edaa-6be3-48b5-80ef-439f3c67b68e" width="600">

- Tab #4 - Spectral Indices Calculation
<img src="https://github.com/user-attachments/assets/f9c83130-e1f3-4a5d-9ed0-397c2d0161cc" width="600">

- Tab #5 - NDVI Time Series Plot
<img src="https://github.com/user-attachments/assets/b8fde949-57e0-440c-a28b-8043f9de22ef" width="400">

- Tab #6 - Principal Component Analysis Calculation
<img src="https://github.com/user-attachments/assets/c943e424-2caa-4e85-ab36-fab8dde354be" width="600">

- Tab #7 - Pansharpening or Image Fusion
<img src="https://github.com/user-attachments/assets/3e549f31-0444-4575-ae36-5e47982b2bd2" width="600">

- Tab #8 - Unsupervised Classification
<img src="https://github.com/user-attachments/assets/fbc2600b-6fbf-4525-bd0b-c805fba66ffb" width="600">

- Tab #9 - Supervised Classification
<img src="https://github.com/user-attachments/assets/6ea203c3-cb4a-4ee6-90a5-25e0f96a7891" width="600">

- Tab #10 - Land Surface Temperature Analysis
<img src="https://github.com/user-attachments/assets/69a7890e-f949-48ad-896d-54274eca0f47" width="600">

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

