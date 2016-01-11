
##connect first
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

import json
baseJSON = {}

##establish connection
connection = getConnection("localhost", "postgres" , "Sequoia93!", "climateHarvest")

def findTableName(connection, datasetName, variableName):
    sql = 'SELECT "tableName" FROM public.vars WHERE "dataSource"='
    sql += "'" + datasetName + "' AND "
    sql += '"variableName"='
    sql += "'" + variableName + "';"
    cursor = connection.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    if len(rows) > 0:
        tName = rows[0][0]
        return tName
    else:
        return False

#table = findTableName(connection, "sdsdss", "TempAsdsdvg")

def queryPoint(connection, x, y, tableName):
    sql = "SELECT ST_Value(rast, ST_SetSRID(ST_MakePoint(" + str(x) + "," + str(y) + "), 4326)) FROM " + tableName
    sql += " WHERE ST_Intersects(rast, ST_SetSRID(ST_MakePoint(" + str(x) + "," + str(y) + "), 4326));"
    cursor = connection.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    value = rows[0][0]
    ##get metadata from vars table
    sql = 'SELECT * FROM public.vars WHERE "tableName"='
    sql += "'" + tableName + "';"
    cursor.execute(sql)
    metadata = cursor.fetchone()
    varID = metadata[0]
    sourceName = metadata[1]
    varName = metadata[2]
    i = {}
    i['dataSource'] = sourceName
    i['varID'] = varID
    i['variable'] = varName
    i['value'] = value
    r = baseJSON
    r['success'] = True
    r['meta'] = (x, y)
    r['data'] = d
    return json.dumps(r)

#queryPoint(connection, -118, 37, table)

def querySources(connection):
    baseSQL = '''SELECT distinct on ("dataSource") "dataSource" FROM public.vars'''
    baseSQL += ''' order by "dataSource"'''
    cursor = connection.cursor()
    cursor.execute(baseSQL)
    results = cursor.fetchall()
    l = []
    for i in results:
        l.append(i[0])
    r = baseJSON
    r['success'] = True
    r['data'] = l
    r['meta'] = "List of all sources in the database"
    return json.dumps(r)

print "Connected."
def queryVariables(connection):
    baseSQL = '''SELECT distinct on ("variableName") "variableName"
        FROM public.vars'''
    baseSQL += ''' order by "variableName"'''
    cursor = connection.cursor()
    cursor.execute(baseSQL)
    results = cursor.fetchall()
    l = []
    for i in results:
        l.append(i[0])
    r = baseJSON
    r['success'] = True
    r['data'] = l
    r['meta'] = "List of all variables in the database"
    return json.dumps(r)


def executeSQL(connection, sql):
    print "Running."
    cursor = connection.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    print rows

#executeSQL(connection, '''SELECT distinct on ("VariableName") "variableName" FROM public.vars''')

def returnValueOfPoint(connection, x, y, tableName):
    ##returns float
    sql = "SELECT ST_Value(rast, ST_SetSRID(ST_MakePoint(" + str(x) + "," + str(y) + "), 4326)) FROM " + tableName
    sql += " WHERE ST_Intersects(rast, ST_SetSRID(ST_MakePoint(" + str(x) + "," + str(y) + "), 4326));"
    cursor = connection.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    if rows != [] and rows != ():
        value = rows[0][0]
    else:
        value = -9999
    return value


table = findTableName(connection, "WorldClim", "BioClim1")

def queryByCSV(connection, csvFile, tableName):
    import csv
    latAliases = ["X", "x", "Latitude", "latitude", "lat", "Lat", "LAT"]
    lngAliases = ["Y", 'y', "Longitude", "long", "longitude", "lng", "LNG", "LNG", "Long", "LONG"]
    reader = csv.DictReader(open(csvFile, 'rU'))
    rows = []
    for row in reader:
        rows.append(row)
    testRow = rows[0]
    keys = testRow.keys()
    latKey = None
    lngKey = None
    for key in keys:
        if key in latAliases:
            latKey = key
        if key in lngAliases:
            lngKey = key
    if latKey is None or lngKey is None:
        return False
    outList = []
    for row in rows:
        p = returnValueOfPoint(connection, row[lngKey], row[lngKey], table)
        outList.append(p)
    return outList

def queryByShapefile(connection, shapefile, tableName):





queryByCSV(connection, "/Users/scottsfarley/documents/testLocs.csv", table)
#queryVariables(connection)

#print queryPoint(connection, -119, 37, table)