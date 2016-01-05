
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

table = findTableName(connection, "sdsdss", "TempAsdsdvg")
print table

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


def queryVariables(connection):
    baseSQL = '''SELECT distinct on ("variableName") "variableName"
        FROM public.climate'''
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

#queryVariables(connection)

#print queryPoint(connection, -119, 37, table)