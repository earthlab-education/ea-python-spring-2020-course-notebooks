# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:light
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.4'
#       jupytext_version: 1.2.4
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

#
# ## <i class="fa fa-graduation-cap" aria-hidden="true"></i> Learning Objectives
#
# * Describe the impacts of cloud cover on analysis of remote sensing data.
# * Use a mask to remove portions of an spectral dataset (image) that is covered by clouds / shadows.
# * Define mask / describe how a mask can be useful when working with remote sensing data.
#
# ## About Landsat Scenes
#
# Landsat satellites orbit the earth continuously collecting images of the Earth's
# surface. These images, are divided into smaller regions - known as scenes.
#
# > Landsat images are usually divided into scenes for easy downloading. Each
# > Landsat scene is about 115 miles long and 115 miles wide (or 100 nautical
# > miles long and 100 nautical miles wide, or 185 kilometers long and 185
# > kilometers wide). -*wikipedia*
#
#
# ### Challenges Working with Landsat Remote Sensing Data
#
# In the previous lessons, you learned how to import a set of geotiffs that made
# up the bands of a Landsat raster. Each geotiff file was a part of a Landsat scene,
# that had been downloaded for this class by your instructor. The scene was further
# cropped to reduce the file size for the class.
#
# You ran into some challenges when you began to work with the data. The biggest
# problem was a large cloud and associated shadow that covered your study
# area of interest - the Cold Springs fire burn scar.
#
# ### Work with Clouds, Shadows and Bad Pixels in Remote Sensing Data
#
# Clouds and atmospheric conditions present a significant challenge when working
# with multispectral remote sensing data. Extreme cloud cover and shadows can make
# the data in those areas, un-usable given reflectance values are either washed out
# (too bright - as the clouds scatter all light back to the sensor) or are too
# dark (shadows which represent blocked or absorbed light).
#
# In this demo you will learn how to deal with clouds in your remote sensing data.
# There is no perfect solution of course. You will just learn one approach.
#

# +
import os
from glob import glob
import matplotlib.pyplot as plt
from matplotlib import patches as mpatches, colors
import seaborn as sns
import numpy as np
import rasterio as rio
from rasterio.plot import plotting_extent
from shapely.geometry import mapping
import earthpy as et
import earthpy.spatial as es
import earthpy.plot as ep
import earthpy.mask as em

# Prettier plotting with seaborn
sns.set_style('white')
sns.set(font_scale=1.5)

# Download data and set working directory
data = et.data.get_data('cold-springs-fire')
os.chdir(os.path.join(et.io.HOME, 'earth-analytics'))
# -

# Next, you will load and plot landsat data. If you are completing the earth analytics course, you have worked with these data already in your homework.
#

# +
landsat_paths_pre_path = os.path.join("data", "cold-springs-fire",
                                      "landsat_collect",
                                      "LC080340322016070701T1-SC20180214145604",
                                      "crop",
                                      "*band*.tif")

landsat_paths_pre = glob(landsat_paths_pre_path)
landsat_paths_pre.sort()

# Stack the Landsat pre fire data
landsat_pre_st_path = os.path.join("data", "cold-springs-fire",
                                   "outputs", "landsat_pre_st.tif")

es.stack(landsat_paths_pre, landsat_pre_st_path)

# Read landsat pre fire data
with rio.open(landsat_pre_st_path) as landsat_pre_src:
    landsat_pre = landsat_pre_src.read(masked=True)
    landsat_extent = plotting_extent(landsat_pre_src)

ep.plot_rgb(landsat_pre,
            rgb=[3, 2, 1],
            extent=landsat_extent,
            title="Landsat True Color Composite Image | 30 meters \n Post Cold Springs Fire \n July 8, 2016")

plt.show()
# -

# Notice in the data above there is a large cloud in your scene. This cloud will impact any quantitative analysis that you perform on the data. You can remove cloudy pixels using a mask. Masking "bad" pixels:
#
# 1. Allows you to remove them from any quantitative analysis that you may perform such as calculating NDVI.
# 2. Allows you to replace them (if you want) with better pixels from another scene. This replacement if often performed when performing time series analysis of data. The following lesson will teach you have to replace pixels in a scene.
#
# ## Cloud Masks in Python
#
# You can use the cloud mask layer to identify pixels that are likely to be clouds
# or shadows. You can then set those pixel values to `masked` so they are not included in
# your quantitative analysis in Python.
#
# When you say "mask", you are talking about a layer that "turns off" or sets to `nan`,
# the values of pixels in a raster that you don't want to include in an analysis.
# It's very similar to setting data points that equal -9999 to `nan` in a time series
# data set. You are just doing it with spatial raster data instead.
#
# <figure>
#     <a href="https://www.earthdatascience.org/images/earth-analytics/raster-data/raster_masks.jpg">
#     <img src="https://www.earthdatascience.org/images/earth-analytics/raster-data/raster_masks.jpg" alt="Raster masks">
#     </a>
# </figure>
#
# *When you use a raster mask, you are defining what pixels you want to exclude from a quantitative analysis. Notice in this image, the raster max is simply a layer that contains values of 1 (use these pixels) and values of NA (exclude these pixels). If the raster is the same extent and spatial resolution as your remote sensing data (in this case your landsat raster stack) you can then mask ALL PIXELS that occur at the spatial location of clouds and shadows (represented by an NA in the image above). Source: Colin Williams (NEON)*
#
#
# * https://landsat.usgs.gov/landsat-8-cloud-cover-assessment-validation-data
# * PDF of the landsat 8 handbook: https://prd-wret.s3.us-west-2.amazonaws.com/assets/palladium/production/atoms/files/LSDS-1574_L8_Data_Users_Handbook-v5.0.pdf

# + {"tags": ["hide"]}
# This is the code for masking

# Create the path for the pixel_qa layer
landsat_pre_cl_path = os.path.join("data", "cold-springs-fire", "landsat_collect",
                                   "LC080340322016070701T1-SC20180214145604", "crop",
                                   "LC08_L1TP_034032_20160707_20170221_01_T1_pixel_qa_crop.tif")

# Open & read the pixel_qa layer for your landsat scene
with rio.open(landsat_pre_cl_path) as landsat_pre_cl:
    landsat_qa = landsat_pre_cl.read(1)
    landsat_ext = plotting_extent(landsat_pre_cl)

# Create a list of values that you want to set as "mask" in the pixel qa layer
high_cloud_confidence = em.pixel_flags["pixel_qa"]["L8"]["High Cloud Confidence"]
cloud = em.pixel_flags["pixel_qa"]["L8"]["Cloud"]
cloud_shadow = em.pixel_flags["pixel_qa"]["L8"]["Cloud Shadow"]

all_masked_values = cloud_shadow + cloud + high_cloud_confidence


# Call the earthpy mask function using pixel QA layer
landsat_pre_cl_free = em.mask_pixels(arr=landsat_pre,
                                     mask_arr = landsat_qa,
                                     vals=all_masked_values)
# -

# Below I walk you through all of the code above so you better understand it.
# However you do NOT need all of the code below to complete any of your homework
# assignments. It just should help you understand what the mask is doing.
#
# ## Raster Masks for Remote Sensing Data
#
# Many remote sensing data sets come with quality layers that you can use as a mask
# to remove "bad" pixels from your analysis. In the case of Landsat, the mask layers
# identify pixels that are likely representative of cloud cover, shadow and even water.
# When you download Landsat 8 data from Earth Explorer, the data came with a processed
# cloud shadow / mask raster layer called `landsat_file_name_pixel_qa.tif`.
# Just replace the name of your Landsat scene with the text landsat_file_name above.
# For this class the layer is:
#
# `LC80340322016189-SC20170128091153/crop/LC08_L1TP_034032_20160707_20170221_01_T1_pixel_qa_crop.tif`
#
# You will explore using this pixel quality assurance (QA) layer, next. To begin, open
# the `pixel_qa` layer using rasterio and plot it with matplotlib.
#

# +
landsat_pre_cl_path = os.path.join("data", "cold-springs-fire",
                                   "landsat_collect",
                                   "LC080340322016070701T1-SC20180214145604",
                                   "crop",
                                   "LC08_L1TP_034032_20160707_20170221_01_T1_pixel_qa_crop.tif")

# Open the pixel_qa layer for your landsat scene
with rio.open(landsat_pre_cl_path) as landsat_pre_cl:
    landsat_qa = landsat_pre_cl.read(1)
    landsat_ext = plotting_extent(landsat_pre_cl)
# -

# First, plot the pixel_qa layer in matplotlib.

# + {"caption": "Landsat Collection Pixel QA layer for the Cold Springs fire area."}
# This is optional code to plot the qa layer - don't worry too much about the details.
# Create a colormap with 11 colors
cmap = plt.cm.get_cmap('tab20b', 11)
# Get a list of unique values in the qa layer
vals = np.unique(landsat_qa).tolist()
bins = [0] + vals
# Normalize the colormap
bounds = [((a + b) / 2) for a, b in zip(bins[:-1], bins[1::1])] + \
    [(bins[-1] - bins[-2]) + bins[-1]]
norm = colors.BoundaryNorm(bounds, cmap.N)

# Plot the data
fig, ax = plt.subplots(figsize=(12, 8))

im = ax.imshow(landsat_qa,
               cmap=cmap,
               norm=norm)

ep.draw_legend(im,
               classes=vals,
               cmap=cmap,
               titles=vals)

ax.set_title("Landsat Collection Quality Assessment Layer")
ax.set_axis_off()
plt.show()
# -

# In the image above, you can see the cloud and the shadow that is obstructing our landsat image.
# Unfortunately for you, this cloud covers a part of your analysis area in the Cold Springs
# Fire location. There are a few ways to handle this issue. We will look at one:
# simply masking out or removing the cloud for your analysis, first.
#
# To remove all pixels that are cloud and cloud shadow covered we need to first
# determine what each value in our qa raster represents. The table below is from the USGS landsat website.
# It describes what all of the values in the pixel_qa layer represent.
#
# You are interested in:
#
# 1. cloud shadow
# 2. cloud and
# 3. high confidence cloud
#
# Note that your specific analysis may require a different set of masked pixels. For instance, your analysis may
# require you identify pixels that are low confidence clouds too. We are just using these classes
# for the purpose of this class.
#
#
# | Attribute                | Pixel Value                                                     |
# |--------------------------|-----------------------------------------------------------------|
# | Fill                     | 1                                                               |
# | Clear                    | 322, 386, 834, 898, 1346                                        |
# | Water                    | 324, 388, 836, 900, 1348                                        |
# | Cloud Shadow             | 328, 392, 840, 904, 1350                                        |
# | Snow/Ice                 | 336, 368, 400, 432, 848, 880, 912, 944, 1352                    |
# | Cloud                    | 352, 368, 416, 432, 480, 864, 880, 928, 944, 992                |
# | Low confidence cloud     | 322, 324, 328, 336, 352, 368, 834, 836, 840, 848, 864, 880      |
# | Medium confidence cloud  | 386, 388, 392, 400, 416, 432, 900, 904, 928, 944                |
# | High confidence cloud    | 480, 992                                                        |
# | Low confidence cirrus    | 322, 324, 328, 336, 352, 368, 386, 388, 392, 400, 416, 432, 480 |
# | High confidence cirrus   | 834, 836, 840, 848, 864, 880, 898, 900, 904, 912, 928, 944, 992 |
# | Terrain occlusion        | 1346, 1348, 1350, 1352                                          |
# ==|
#
# To better understand the values above, create a better map of the data. To do that you will:
#
# 1. classify the data into x classes where x represents the total number of unique values in the `pixel_qa` raster.
# 2. plot the data using these classes.
#
# We are reclassifying the data because matplotlib colormaps will assign colors to values along a continuous gradient.
# Reclassifying the data allows us to enforce one color for each unique value in our data.
#

# This next section shows you how to create a mask using the earthpy mask helper function `_create_mask` to create a binary cloud mask layer. In this mask all pixels that you wish to remove from your analysis or mask will be set to `1`. All other pixels which represent pixels you want to use in your analysis will be set to `0`.
#
# ### NOTE:
# This step can be done by changing the inputs into the main `mask_pixels` function. We include it here so you can see what is going on in the function. See lower down in the lesson for this call.

# +
# You can grab the cloud pixel values from earthpy
high_cloud_confidence = em.pixel_flags["pixel_qa"]["L8"]["High Cloud Confidence"]
cloud = em.pixel_flags["pixel_qa"]["L8"]["Cloud"]
cloud_shadow = em.pixel_flags["pixel_qa"]["L8"]["Cloud Shadow"]

all_masked_values = cloud_shadow + cloud + high_cloud_confidence
all_masked_values
# -

# This is using a helper function from earthpy to create the mask so we can plot it
# You don't need to do this in your workflow as you can perform the mask in one step
# But we have it here for demonstration purposes
cl_mask = em._create_mask(landsat_qa, all_masked_values)
np.unique(cl_mask)

# Below is the plot of the reclassified raster mask created from the `_create_mask` helper function.

# + {"caption": "Landsat image in which the masked pixels (cloud) are rendered in light purple.", "tags": ["hide"]}
fig, ax = plt.subplots(figsize=(12, 8))

im = ax.imshow(cl_mask,
               cmap=plt.cm.get_cmap('tab20b', 2))

cbar = ep.colorbar(im)
cbar.set_ticks((0.25, .75))
cbar.ax.set_yticklabels(["Clear Pixels", "Cloud / Shadow Pixels"])

ax.set_title("Landsat Cloud Mask | Light Purple Pixels will be Masked")
ax.set_axis_off()

plt.show()
# -

# ## What Does the Metadata Tell You?
#
# You just explored two layers that potentially have information about cloud cover.
# However what do the values stored in those rasters mean? You can refer to the
# metadata provided by USGS to learn more about how
# each layer in your landsat dataset are both stored and calculated.
#
# When you download remote sensing data, often (but not always), you will find layers
# that tell us more about the error and uncertainty in the data. Often whomever
# created the data will do some of the work for us to detect where clouds and
# shadows are - given they are common challenges that you need to work around when
# using remote sensing data.
#
#
# ### Create Mask Layer in Python
#
# To create the mask this you do the following:
#
# 1. Make sure you use a raster layer for the mask that is the SAME EXTENT and the same pixel resolution as your landsat scene. In this case you have a mask layer that is already the same spatial resolution and extent as your landsat scene.
# 2. Set all of the values in that layer that are clouds and / or shadows to `1` (1 to represent `mask = True`)
# 3. Finally you use the `masked_array` function to apply the mask layer to the numpy array (or the landsat scene that you are working with in Python).  all pixel locations that were flagged as clouds or shadows in your mask to `NA` in your `raster` or in this case `rasterstack`.
#
# ## Mask A Landsat Scene Using EarthPy
# Below you mask your data in one single step. This function `em.mask_pixels()` creates the mask as you saw above and then masks your data.

# Call the earthpy mask function using your mask layer
landsat_pre_cl_free = em.mask_pixels(landsat_pre, cl_mask)

# Alternatively, you can directly input your mask values and the pixel QA layer into the `mask_pixels` function. This is the easiest way to mask your data!

# Call the earthpy mask function using pixel QA layer
landsat_pre_cl_free = em.mask_pixels(landsat_pre, 
                                     landsat_qa, 
                                     vals=all_masked_values)

# + {"caption": "CIR Composite image in grey scale with mask applied, covering the post-Cold Springs fire area on July 8, 2016."}
# Plot the data
ep.plot_bands(landsat_pre_cl_free[6],
              extent=landsat_extent,
              cmap="Greys",
              title="Landsat CIR Composite Image | 30 meters \n Post Cold Springs Fire \n July 8, 2016",
              cbar=False)
plt.show()

# + {"caption": "CIR Composite image with cloud mask applied, covering the post-Cold Springs fire area on July 8, 2016."}
# Plot data
ep.plot_rgb(landsat_pre_cl_free,
            rgb=[4, 3, 2],
            extent=landsat_ext,
            title="Landsat CIR Composite Image | 30 meters \n Post Cold Springs Fire \n July 8, 2016")
plt.show()
