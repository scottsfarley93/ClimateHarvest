__author__ = 'scottsfarley'
import gdal
import gdalconst
import sys
import numpy
import osgeo
import osr

fname = "/Users/scottsfarley/downloads/prism/PRISM_ppt_30yr_normal_4kmM2_annual_asc.asc"
raster = datasource = gdal.Open(fname, 0)
band = datasource.GetRasterBand(1)
data = band.ReadAsArray().astype(numpy.float)


xsize = datasource.RasterXSize
ysize = datasource.RasterYSize
transform = raster.GetGeoTransform()
pixelWidth = transform[1]
pixelHeight = transform[5]
cols = raster.RasterXSize
rows = raster.RasterYSize

rasterLeft = transform[0]
rasterTop = transform[3]
rasterRight = rasterLeft+cols*pixelWidth
rasterBottom = rasterTop-rows*pixelHeight
coords = []

colStart = rasterLeft
i = 0
for col in data:
    rowStart = rasterTop
    rowCoords = []
    j = 0
    for row in data:
        cellTop = rowStart
        cellBottom = rowStart + pixelHeight
        cellRight = colStart + pixelWidth
        cellLeft = colStart
        c = [cellTop, cellRight, cellBottom, cellLeft]
        rowCoords.append(c)

        rowStart += pixelHeight
        j += 1
    coords.append(rowCoords)
    colStart += pixelWidth
    i += 1

# for i in coords:
#     print i



