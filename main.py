
def getConnection(host, username, password, database):
    """Connect to database and return the connection cursor to allow insertion"""
    import psycopg2
    try:
        connectString = "dbname='" + str(database) + "' user='" + str(username) + "' host='" + str(host) + "' password='" + str(password) + "'"
        conn = psycopg2.connect(connectString)
        return conn
    except:
        print "I am unable to connect to the database"
        return False

##establish connection
connection = getConnection("localhost", "postgres" , "Sequoia93!", "climateHarvest")

def ingestRaster(connection, rasterSource, variableName, sourceName):
    """Ingest a raster and translate it into a database table format
        DatabaseConnection: connection cursor
        rasterName: name of raster dataset on disk.  Returns an error if this dataset does not exit.
        variableName: Name of variable represented by raster dataset (meanTemp, temp1, meanPrecip, etc)
        sourceName: Name of dataset source (Prism, worldclim, etc)
    """
    import gdal
    import numpy
    import progressbar


    ##connect to database
    cursor = connection.cursor()


    fname = rasterSource
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

    widgets = ['Ingesting. Estimated Time Remaining : ', progressbar.ETA(), " Row ", progressbar.Counter() , " of " , str(len(data)) ]
    count = 0
    progress = progressbar.ProgressBar(widgets=widgets, maxval=len(data))
    progress.start()
    colStart = rasterLeft
    i = 0
    for col in data:
        rowStart = rasterTop
        rowCoords = []
        j = 0
        for row in col:
            if row != -9999:
                cellTop = rowStart
                cellBottom = rowStart + pixelHeight
                cellRight = colStart + pixelWidth
                cellLeft = colStart
                c = [cellTop, cellRight, cellBottom, cellLeft]
                avgY = cellTop + cellBottom / 2
                avgX = cellRight + cellLeft / 2
                geom_statement = "'POLYGON((" + str(cellLeft) + " " + str(cellTop) + "," + str(cellRight) + " " + str(cellTop) + \
                    "," + str(cellRight) + " " + str(cellBottom) + "," + str(cellLeft) + " " + str(cellBottom) + "," \
                                 + str(cellLeft) + "  " + str(cellTop) + "))'"
                test_geom = "'POLYGON((-71.1776585052917 42.3902909739571,-71.1776820268866 42.3903701743239,-71.1776063012595 42.3903825660754,-71.1775826583081 42.3903033653531,-71.1776585052917 42.3902909739571))'"

                sql = "INSERT INTO climate VALUES (DEFAULT, " \
                      " '" + variableName + "', '" + sourceName + "', " + str(row) + ", " \
                      "ST_SetSRID(ST_MakePoint(" + str(avgX) + ", " + str(avgY) + "), 4326), " \
                      "ST_SetSRID(ST_GeomFromText(" + geom_statement + "), 4326));"


                cursor.execute(sql)

                rowStart += pixelHeight
                j += 1

        coords.append(rowCoords)
        colStart += pixelWidth
        progress.update(i)
        i += 1
    connection.commit()
    print "Added all rows."
    print "New Count is: "
    sql = "SELECT COUNT(*) FROM climate"
    cursor.execute(sql)
    rows = cursor.fetchall()
    print rows[0]


#ingestRaster(connection, "/Users/scottsfarley/downloads/prism/PRISM_ppt_30yr_normal_4kmM2_annual_asc.asc", "PRISM", "PrecipTotal")




def queryDatabase(connection, sqlQuery):
    cursor = connection.cursor()
    cursor.execute(sqlQuery)
    rows = cursor.fetchall()
    return rows

def queryPoint(x, y, dataset = "", variable = ""):
    baseSQL = sql = '''SELECT "cellID", "dataSource", variable, value, ST_AsText(point), ST_AsText(box) FROM climate
                  WHERE ST_Intersects(ST_SetSRID(ST_MakePoint(''' + str(x) + ''',''' + str(y) + '''), 4326), box)'''
    if dataset != "":
        var = "'" + str(dataset) + "'"
        baseSQL += ''' AND "dataSource"=''' + var
    if variable != "":
        var = "'" + str(variable) + "'" ##get quotes right
        baseSQL += ''' AND "variable"=''' + var
    results =  queryDatabase(connection, baseSQL)
    print baseSQL
    print "Number of results: ", str(len(results))
    if len(results) != 0:
        value = results[0][3]
        return value
    else:
        return False



def queryPointWithRadius(x, y, radius):
    sql = '''SELECT "cellID", "dataSource", variable, value, ST_AsText(point), ST_AsText(box) FROM climate
         WHERE ST_DWithin(ST_SetSRID(ST_MakePoint(''' + str(x) + ''',''' + str(y) + '''), 4326), box, ''' + str(radius) + ''');'''
    results =   queryDatabase(connection, sql)
    for i in results:
        print i
    print "Found: " + str(len(results)/2)



def getSiteCoords():
    import json
    import urllib2
    url = "http://api.neotomadb.org/v1/data/sites/?gpid=9227"
    response = urllib2.urlopen(url)
    data = json.load(response)
    lats = []
    lngs = []
    for row in data['data']:
        lat1 = row['LatitudeNorth']
        lat2 = row['LatitudeSouth']
        lng1 = row['LongitudeWest']
        lng2 = row['LongitudeEast']
        if lat1 is None or lat2 is None or lng1 is None or lng2 is None:
            continue
        else:
            avgLat = (lat1 +  lat2) / 2
            avgLng = (lng1 + lng2) / 2
            lats.append(avgLat)
            lngs.append(avgLng)
    print "I now have coordinates for " + str(len(lats)) + " sites."
    return [lats, lngs]

coords = getSiteCoords()
lats = coords[0]
lngs = coords[1]
temps = []
precips = []
i = 0
while i < len(lats):
    lat = lats[i]
    lng = lngs[i]
    tVal =  queryPoint(lng, lat, dataset="TempAvg")
    pVal = queryPoint(lng, lat, dataset="PrecipTotal")
    if tVal and pVal:
        temps.append(tVal)
        precips.append(pVal)
    i +=1


print "Collected ", len(temps), " temperature values."
import matplotlib.pyplot as plt
plt.plot(temps, precips, 'ro')
plt.xlabel("Mean Temperature")
plt.ylabel("Total Precipitation")
plt.title("Neotoma Sites in Wisconsin")
plt.show()










