import json
import cherrypy
import os
import csv



baseJSON = {'success' : False, 'message' : None, 'data' : None, 'meta' : None, "timeslice": 0}

def getConnection(host, username, password, database):
    """Connect to database and return the connection cursor to allow insertion"""
    import psycopg2
    try:
        connectString = "dbname='" + str(database) + "' user='" + str(username) + "' host='" + str(host) + "' password='" + str(password) + "'"
        conn = psycopg2.connect(connectString)
        return conn
    except:
        return False

def queryDatabase(connection, sqlQuery):
    cursor = connection.cursor()
    cursor.execute(sqlQuery)
    rows = cursor.fetchall()
    cursor.close()
    return rows

def findTableName(connection, datasetName, variableName, timeslice):
    sql = 'SELECT "tableName" FROM public.vars WHERE "dataSource"='
    sql += "'" + datasetName + "' AND "
    sql += '"variableName"='
    sql += "'" + variableName + "'"
    sql += '''AND "time"=''' + str(timeslice) + ";"
    cursor = connection.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    cursor.close()
    baseJSON['timeslice'] = timeslice
    if len(rows) > 0:
        tName = rows[0][0]
        return tName
    else:
        return False

def queryPoint(connection, x, y, tableName):
    ##returns json
    sql = "SELECT ST_Value(rast, ST_SetSRID(ST_MakePoint(" + str(x) + "," + str(y) + "), 4326)) FROM " + tableName
    sql += " WHERE ST_Intersects(rast, ST_SetSRID(ST_MakePoint(" + str(x) + "," + str(y) + "), 4326));"
    cursor = connection.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    if rows != [] and rows != ():
        value = rows[0][0]
    else:
        value = -1
    ##get metadata from vars table
    sql = 'SELECT * FROM public.vars WHERE "tableName"='
    sql += "'" + tableName + "';"
    cursor.execute(sql)
    metadata = cursor.fetchone()
    if metadata != ():
        varID = metadata[0]
        sourceName = metadata[1]
        varName = metadata[3]
        i = {}
        i['dataSource'] = sourceName
        i['varID'] = varID
        i['variable'] = varName
        i['value'] = value
        r = baseJSON
        r['success'] = True
        r['meta'] = (x, y)
        r['data'] = i
        cursor.close()
        return json.dumps(r)
    else:
        return False

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


def querySources(connection, timeslice):
    baseSQL = '''SELECT distinct on ("dataSource") "dataSource" FROM public.vars '''
    baseSQL += '''WHERE "time"=''' + str(timeslice)
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
    r['timeslice'] = timeslice
    r['meta'] = "List of all sources in the database"
    cursor.close()
    return json.dumps(r)


def queryVariables(connection, dataset="", timeslice=0):
    baseSQL = '''SELECT distinct on ("variableName") "variableName"
        FROM public.vars '''
    if dataset != "":
        baseSQL += '''WHERE "dataSource"='''
        baseSQL += "'" + dataset + "'"
    baseSQL += ''' AND "time"=''' + str(timeslice)
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
    r['timeslice'] = timeslice
    cursor.close()
    return json.dumps(r)

def queryTime(connection):
    sql = '''SELECT distinct on ("time") "time" from public.vars;'''
    cursor = connection.cursor()
    cursor.execute(sql)
    results = cursor.fetchall()
    l = []
    for i in results:
        l.append(i[0])
    r = baseJSON
    r['success'] = True
    r['data'] = l
    r['timeslice'] = None
    r['meta'] = "List of all timeslices in the database"
    cursor.close()
    return json.dumps(r)

def queryAllLayers(connection, latitude, longitude):
    ##list all table names
    cursor = connection.cursor()
    sql = '''SELECT * FROM public.vars ORDER BY "time"'''
    cursor.execute(sql)
    rows = cursor.fetchall()
    r = baseJSON
    r['success'] = True
    r['timeslice'] = None
    outList = []
    r['meta'] = "Values for x/y pair in all tables of database."
    for row in rows:
        tableName = row[6]
        time = row[8]
        val = returnValueOfPoint(connection, longitude, latitude, tableName)
        out = {
            "timeslice": time,
            "source": row[1],
            "variable": row[3],
            "value": val,
        }
        outList.append(out)
    r['data'] = outList
    return json.dumps(r)





##the Connection
conn = getConnection('localhost', 'postgres', 'Sequoia93!', 'climateHarvest')



class API(object):
    @cherrypy.expose
    def index(self):
        return open("index.html")
    @cherrypy.expose
    def getData(self, latitude=0, longitude=0, datasource="", variable="", timeslice=0):
        if not conn:
            return str(json.dumps(baseJSON))
        ##get the table first
        table = findTableName(conn, datasource, variable, timeslice)
        p = queryPoint(conn, longitude, latitude, table)
        print p
        return str(p)

    @cherrypy.expose
    def getAllVariables(self, dataset="ALL", timeslice=0):
        if not conn:
            return str(json.dumps(baseJSON))
        if dataset=="ALL":
            dataset = ""
        l = queryVariables(conn, dataset, timeslice)
        return str(l)

    @cherrypy.expose
    def getAllSources(self, timeslice=0):
        if not conn:
            return str(json.dumps(baseJSON))
        l = querySources(conn, timeslice)
        return str(l)

    @cherrypy.expose
    def neotomaQuery(self):
        return open('neotomaSearch.html')

    @cherrypy.expose
    def graph(self):
        return open("graphView.html")

    @cherrypy.expose
    def getAllTimes(self):
        if not conn:
            return str(json.dumps(baseJSON))
        l = queryTime(conn)
        return str(l)

    @cherrypy.expose
    def map(self):
        return open("map.html")

    @cherrypy.expose
    def queryAllLayers(self, latitude, longitude):
        if not conn:
            return str(json.dumps(baseJSON))
        l = queryAllLayers(conn, latitude, longitude)
        return str(l)

    @cherrypy.expose
    def uploadCSV(self):
        cl = cherrypy.request.body.params
        return cl
        return "Got to server."

    @cherrypy.expose
    def uploadFileTest(self):
        return open("uploadFile.html")




def CORS():
    cherrypy.response.headers["Access-Control-Allow-Origin"] = "*"



if __name__ == '__main__':
    cherrypy.tools.CORS = cherrypy.Tool('before_handler', CORS)
    conf = {

    '/': {
        #'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
        'tools.sessions.on': True,
        'tools.response_headers.on': True,
        #'tools.CORS.on': True,
        #'tools.response_headers.headers': [('Content-Type', 'text/plain')],
        }
    }
    #cherrypy.tools.CORS = cherrypy.Tool('before_handler', CORS)
    #cherrypy.config.update({'server.socket_port': 8080})

    cherrypy.quickstart(API(), "/", conf)