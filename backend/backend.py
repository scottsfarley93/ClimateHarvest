import cherrypy
import psycopg2
from time import strftime
import json

def connectToDatabase(hostname, username, password, database):
    try:
        connectString = "dbname='" + str(database) + "' user='" + str(username) + "' host='" + str(hostname) + "' password='" + str(password) + "'"
        conn = psycopg2.connect(connectString)
        return conn
    except:
        print "I am unable to connect to the database"
        return False

def closeConnection(connection):
    try:
        connection.close()
        return True
    except:
        print "Failed to close connection."
        return False


returnJSON = {
    'success' : False,
    'meta' : {
        'args' : {},
        'timestamp' : None,
        'message' : None,
    },
    'data' : None
}

def logRequest(resource, method, requestHeaders):
    connection = connectToDatabase("localhost", "postgres" , "Sequoia93!", "climateHarvest")
    cursor = connection.cursor()
    address = requestHeaders['Remote-Addr']
    sql = '''INSERT INTO "Requests" VALUES ('''
    sql += "DEFAULT, DEFAULT, '" + str(address) + "', '" + str(resource)  + "','" + method + "')"
    cursor.execute(sql)
    connection.commit()
    connection.close()


unsupportedMethodString = "Call was to an unsupported method.  Check the documentation for this resource."

def getTableList(connection, source, variable, timeslice):
    sql = 'SELECT * FROM public.vars'
    if source is not None or variable is not None or timeslice is not None:
        sql += " WHERE"
    if source is not None:
        sql += ''' "dataSource"='''
        sql += "'" + source + "'"
        if variable is not None or timeslice is not None:
            sql += " AND"
    if variable is not None:
        sql += ''' "variableName"='''
        sql += "'" + variable + "'"
        if timeslice is not None:
            sql += " AND"
    if timeslice is not None:
        sql +=  ''' "time"=''' + str(timeslice)
    cursor = connection.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    return rows


def getTables(connection, source, variable, timeslice):
    out = returnJSON
    ##these are the same whether or not the call failes
    out['meta']['timestamp'] = str(strftime("%Y-%m-%d %H:%M:%S"))
    out['meta']['args'] = {"source" :str(source), "variable":str(variable), "timeslice" : str(timeslice), "connection" :str(connection)}
    try:
        rows = getTableList(connection, source, variable, timeslice)
        ##successful response parameters
        out['meta']['message'] = "Request fulfilled successfully."
       ## build data json
        dataOut = []
        i = 0
        while i < len(rows):
            row = rows[i]
            rowOut = {
                'tableID' : row[0],
                'dataSource' : row[1],
                'varCode' : row[2],
                'varName' : row[3],
                'tileX' : row[4],
                'tileY' : row[5],
                'tableName' : row[6],
                'lastModified' : str(row[7]),
                'timeslice' : row[8]
            }
            dataOut.append(rowOut)
            i += 1
        out['data'] = dataOut
        out['success'] = True
        return out
    except Exception as E:
        out['meta']['message'] = str(E)
        return out


def getData(connection, latitude, longitude, source, variable, timeslice):
    out = returnJSON
    out['meta']['args'] = {'source' : source, 'variable' : variable, 'timeslice' : timeslice, 'latitude' : latitude, 'longitude' : longitude}
    if latitude is None or longitude is None:
        out['message'] = "Latitude and longitude must be specified as parameters."
        return out
    ##get the table list that meets the source, variable, timeslice criteria
    ##then query those tables for lat/lng pair
    dbOut = []
    try:
        tables = getTableList(connection, source, variable, timeslice)
        sql = ""
        for table in tables:
            cursor = connection.cursor()
            tableName = table[6]
            varName = table[3]
            varCode = table[2]
            dataSource = table[1]
            tableID = table[0]
            tileX = table[4]
            tileY = table[5]
            lastMod = str(table[7])
            timeslice = table[8]
            sql = "SELECT ST_Value(rast, ST_SetSRID(ST_MakePoint(" + str(latitude) + "," + str(longitude) + "), 4326)) FROM " + tableName
            sql += " WHERE ST_Intersects(rast, ST_SetSRID(ST_MakePoint(" + str(latitude) + "," + str(longitude) + "), 4326));"
            cursor.execute(sql)
            row = cursor.fetchone()
            value = row[0]
            rowOut = {
                'varName' : varName,
                'varCode' : varCode,
                'tableID' : tableID,
                'tableName' : tableName,
                'tileX' : tileX,
                'tileY' : tileY,
                'lastModified' : lastMod,
                'timeslice' : timeslice,
                'dataSouce' : dataSource,
                'value' : value,
                'latitude' : latitude,
                'longitude': longitude
            }
            print sql
            dbOut.append(rowOut)
            cursor.close()
        out['data'] = dbOut
        out['success'] = True
        out['meta']['message'] = "Request fulfilled successfully."
        return out
    except Exception as E:
        out['meta']['message'] = str(E)
        return str(E)


def getSources(connection, variable, timeslice):
    out = returnJSON
    out['meta']['timestamp'] = str(strftime("%Y-%m-%d %H:%M:%S"))
    out['meta']['args'] = {'variable' : variable, 'timeslice' : timeslice}
    sql = '''SELECT distinct on ("dataSource") "dataSource" FROM public.vars'''
    if variable is not None or timeslice is not None:
        sql += " WHERE "
    if variable is not None:
        sql += ''' "variableName'='''
        sql += str(variable)
        if timeslice is not None:
            sql += " AND "
    if timeslice is not None:
        sql += ''' "time"='''
        sql += str(timeslice)
    sql += ' ORDER BY "dataSource"'
    try:
        cursor = connection.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        dbOut = []
        for row in rows:
            outRow = {
                'sourceName' : row[0]
            }
            dbOut.append(outRow)
        out['meta']['message'] = "Request fulfilled successfully."
        out['success'] = True
        out['data'] = dbOut
        return out
    except Exception as e:
        out['meta']['message'] = str(e)
        return out



def getVariables(connection, source, timeslice):
    out = returnJSON
    out['meta']['timestamp'] = str(strftime("%Y-%m-%d %H:%M:%S"))
    out['meta']['args'] = {'source' : source, 'timeslice' : timeslice}
    sql = '''SELECT distinct on ("variableName") "variableName" FROM public.vars'''
    if source is not None or timeslice is not None:
        sql += " WHERE "
    if source is not None:
        sql += ''' "dataSource"='''
        sql += "'"
        sql += str(source)
        if timeslice is not None:
            sql += "' AND "
    if timeslice is not None:
        sql += ''' "time"='''
        sql += str(timeslice)
    sql += ' ORDER BY "variableName"'
    print sql
    try:
        cursor = connection.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        dbOut = []
        for row in rows:
            outRow = {
                'variableName' : row[0]
            }
            dbOut.append(outRow)
        out['meta']['message'] = "Request fulfilled successfully."
        out['success'] = True
        out['data'] = dbOut
        return out
    except Exception as e:
        out['meta']['message'] = str(e)
        return out

def getTimeslices(connection, source, variable):
    out = returnJSON
    out['meta']['timestamp'] = str(strftime("%Y-%m-%d %H:%M:%S"))
    out['meta']['args'] = {'source' : source, 'variable' : variable}
    sql = '''SELECT distinct on ("time") "time" FROM public.vars'''
    if source is not None or variable is not None:
        sql += " WHERE "
    if source is not None:
        sql += ''' "dataSource"='''
        sql += "'" +  str(source) + "'"
        if variable is not None:
            sql += " AND "
    if variable is not None:
        sql += ''' "time"='''
        sql += str(variable)
    sql += ' ORDER BY "time"'
    try:
        cursor = connection.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        dbOut = []
        for row in rows:
            outRow = {
                'timeslice' : row[0]
            }
            dbOut.append(outRow)
        out['meta']['message'] = "Request fulfilled successfully."
        out['success'] = True
        out['data'] = dbOut
        return out
    except Exception as e:
        out['meta']['message'] = str(e)
        return out



class Tables:

    exposed = True

    def GET(self, source=None, variable=None, timeslice=None, tileX=None, tileY=None, *args, **kwargs):
        if kwargs != {}:
            response = returnJSON
            response['meta']['message'] = str(kwargs.keys()[0]) + " is not a valid parameter list for this resource. This method accepts the following" \
                                                   " input parameters: source, variable, timeslice, tileX, tileY"
            response['meta']['timestamp'] = str(strftime("%Y-%m-%d %H:%M:%S"))
        else:
            connection = connectToDatabase("localhost", "postgres" , "Sequoia93!", "climateHarvest")
            response = getTables(connection, source, variable, timeslice)
            headers = cherrypy.request.headers
            logRequest("Tables", "GET", headers)
            connection.close()
        return str(json.dumps(response))

    def PUT(self, *args):
        out = returnJSON
        out['meta']['message'] = unsupportedMethodString
        out['timestamp'] = out['meta']['timestamp'] = str(strftime("%Y-%m-%d %H:%M:%S"))
        logRequest("Tables", "PUT",  cherrypy.request.headers)
        return str(json.dumps(out))

    def POST(self, *args):
        out = returnJSON
        out['meta']['message'] = unsupportedMethodString
        out['timestamp'] = out['meta']['timestamp'] = str(strftime("%Y-%m-%d %H:%M:%S"))
        logRequest("Tables", "POST",  cherrypy.request.headers)
        return str(json.dumps(out))

    def DELETE(self, *args):
        out = returnJSON
        out['meta']['message'] = unsupportedMethodString
        out['timestamp'] = out['meta']['timestamp'] = str(strftime("%Y-%m-%d %H:%M:%S"))
        logRequest("Tables", "DELETE",  cherrypy.request.headers)
        return str(json.dumps(out))


class Data:

    exposed = True

    def GET(self, latitude=None, longitude=None, source=None, variable=None, timeslice=None, *args, **kwargs):
        if kwargs != {}:
            response = returnJSON
            response['meta']['message'] = str(kwargs.keys()[0]) + " is not a valid parameter list for this resource. This method accepts the following" \
                                                   " input parameters: latitude, longitude, source, variable, timeslice"
            response['meta']['timestamp'] = str(strftime("%Y-%m-%d %H:%M:%S"))
        else:
            connection = connectToDatabase("localhost", "postgres" , "Sequoia93!", "climateHarvest")
            response = getData(connection, longitude, latitude, source, variable, timeslice)
            logRequest("Data", "GET",  cherrypy.request.headers)
            connection.close()
        return str(json.dumps(response))

    def PUT(self, *args):
        out = returnJSON
        out['meta']['message'] = unsupportedMethodString
        out['timestamp'] = out['meta']['timestamp'] = str(strftime("%Y-%m-%d %H:%M:%S"))
        logRequest("Data", "PUT",  cherrypy.request.headers)
        return str(json.dumps(out))

    def POST(self, *args):
        out = returnJSON
        out['meta']['message'] = unsupportedMethodString
        out['timestamp'] = out['meta']['timestamp'] = str(strftime("%Y-%m-%d %H:%M:%S"))
        logRequest("Data", "POST",  cherrypy.request.headers)
        return str(json.dumps(out))

    def DELETE(self, *args):
        out = returnJSON
        out['meta']['message'] = unsupportedMethodString
        out['timestamp'] = out['meta']['timestamp'] = str(strftime("%Y-%m-%d %H:%M:%S"))
        logRequest("Data", "DELETE",  cherrypy.request.headers)
        return str(json.dumps(out))


class Sources:

    exposed = True

    def GET(self, variable=None, timeslice=None, *args, **kwargs):
        if kwargs != {}:
            response = returnJSON
            response['meta']['message'] = str(kwargs.keys()[0]) + " is not a valid parameter list for this resource. This method accepts the following" \
                                                   " input parameters: variable, timeslice"
            response['meta']['timestamp'] = str(strftime("%Y-%m-%d %H:%M:%S"))
        else:
            connection = connectToDatabase("localhost", "postgres" , "Sequoia93!", "climateHarvest")
            response = getSources(connection, variable, timeslice)
            headers = cherrypy.request.headers
            logRequest("Sources", "GET",  cherrypy.request.headers)
            connection.close()
        return str(json.dumps(response))

    def PUT(self, *args):
        out = returnJSON
        out['meta']['message'] = unsupportedMethodString
        out['timestamp'] = out['meta']['timestamp'] = str(strftime("%Y-%m-%d %H:%M:%S"))
        logRequest("Sources", "PUT",  cherrypy.request.headers)
        return str(json.dumps(out))

    def POST(self, *args):
        out = returnJSON
        out['meta']['message'] = unsupportedMethodString
        out['timestamp'] = out['meta']['timestamp'] = str(strftime("%Y-%m-%d %H:%M:%S"))
        logRequest("Sources", "POST",  cherrypy.request.headers)
        return str(json.dumps(out))

    def DELETE(self, *args):
        out = returnJSON
        out['meta']['message'] = unsupportedMethodString
        out['timestamp'] = out['meta']['timestamp'] = str(strftime("%Y-%m-%d %H:%M:%S"))
        logRequest("Sources", "DELETE",  cherrypy.request.headers)
        return str(json.dumps(out))


class Variables:

    exposed = True

    def GET(self, source=None, timeslice=None, *args, **kwargs):
        if kwargs != {}:
            response = returnJSON
            response['meta']['message'] = str(kwargs.keys()[0]) + " is not a valid parameter list for this resource. This method accepts the following" \
                                                   " input parameters: source, timeslice"
            response['meta']['timestamp'] = str(strftime("%Y-%m-%d %H:%M:%S"))
        else:
            connection = connectToDatabase("localhost", "postgres" , "Sequoia93!", "climateHarvest")
            response = getVariables(connection, source, timeslice)
            headers = cherrypy.request.headers
            logRequest("Variables", "GET",  cherrypy.request.headers)
            connection.close()
        return str(json.dumps(response))

    def PUT(self, *args):
        out = returnJSON
        out['meta']['message'] = unsupportedMethodString
        out['timestamp'] = out['meta']['timestamp'] = str(strftime("%Y-%m-%d %H:%M:%S"))
        logRequest("Variables", "PUT",  cherrypy.request.headers)
        return str(json.dumps(out))

    def POST(self, *args):
        out = returnJSON
        out['meta']['message'] = unsupportedMethodString
        out['timestamp'] = out['meta']['timestamp'] = str(strftime("%Y-%m-%d %H:%M:%S"))
        logRequest("Variables", "POST",  cherrypy.request.headers)
        return str(json.dumps(out))

    def DELETE(self, *args):
        out = returnJSON
        out['meta']['message'] = unsupportedMethodString
        out['timestamp'] = out['meta']['timestamp'] = str(strftime("%Y-%m-%d %H:%M:%S"))
        logRequest("Variables", "DELETE",  cherrypy.request.headers)
        return str(json.dumps(out))



class Timeslices:

    exposed = True

    def GET(self,  source=None, variable=None, *args, **kwargs):
        if kwargs != {}:
            response = returnJSON
            response['meta']['message'] = str(kwargs.keys()[0]) + " is not a valid parameter list for this resource. This method accepts the following" \
                                                   " input parameters: source, variable"
            response['meta']['timestamp'] = str(strftime("%Y-%m-%d %H:%M:%S"))
        else:
            connection = connectToDatabase("localhost", "postgres" , "Sequoia93!", "climateHarvest")
            response = getTimeslices(connection, source, variable)
            headers = cherrypy.request.headers
            logRequest("Timeslices", "GET",  cherrypy.request.headers)
            connection.close()
        return str(json.dumps(response))

    def PUT(self, *args):
        out = returnJSON
        out['meta']['message'] = unsupportedMethodString
        out['timestamp'] = out['meta']['timestamp'] = str(strftime("%Y-%m-%d %H:%M:%S"))
        logRequest("Timeslices", "PUT",  cherrypy.request.headers)
        return str(json.dumps(out))

    def POST(self, *args):
        out = returnJSON
        out['meta']['message'] = unsupportedMethodString
        out['timestamp'] = out['meta']['timestamp'] = str(strftime("%Y-%m-%d %H:%M:%S"))
        logRequest("Timeslices", "POST",  cherrypy.request.headers)
        return str(json.dumps(out))

    def DELETE(self, *args):
        out = returnJSON
        out['meta']['message'] = unsupportedMethodString
        out['timestamp'] = out['meta']['timestamp'] = str(strftime("%Y-%m-%d %H:%M:%S"))
        logRequest("Timeslices", "DELETE",  cherrypy.request.headers)
        return str(json.dumps(out))

class Root:
    exposed = True

    def GET(self, *args, **kwargs):
        out = returnJSON
        out['meta']['timestamp'] = str(strftime("%Y-%m-%d %H:%M:%S"))
        out['meta']['message'] = "This service contains no resource named " + str(args[0])
        return str(json.dumps(out))

    def PUT(self, *args):
        out = returnJSON
        out['meta']['timestamp'] = str(strftime("%Y-%m-%d %H:%M:%S"))
        out['meta']['message'] = "This service contains no resource named " + str(args[0])
        return str(json.dumps(out))

    def POST(self, *args):
        out = returnJSON
        out['meta']['timestamp'] = str(strftime("%Y-%m-%d %H:%M:%S"))
        out['meta']['message'] = "This service contains no resource named " + str(args[0])
        return str(json.dumps(out))

    def DELETE(self, *args):
        out = returnJSON
        out['meta']['timestamp'] = str(strftime("%Y-%m-%d %H:%M:%S"))
        out['meta']['message'] = "This service contains no resource named " + str(args[0])
        return str(json.dumps(out))

##bug fix
class Index:
    exposed = True
    def GET(self, *args, **kwargs):
        return open("index.html")


class NeotomaSearch:
    exposed = True
    def GET(self, *args, **kwargs):
        return open("neotomaSearch.html")

class Map:
    exposed = True
    def GET(self, *args, **kwargs):
        return open("map.html")

class GraphView:
    exposed = True
    def GET(self, *args, **kwargs):
        return open("graphView.html")




if __name__ == '__main__':
    cherrypy.tree.mount(
        Data(), '/api/data',
        {'/':
            {'request.dispatch': cherrypy.dispatch.MethodDispatcher()}
        }
    )
    cherrypy.tree.mount(
        Tables(), '/api/tables',
        {'/':
            {'request.dispatch': cherrypy.dispatch.MethodDispatcher()}
        }
    )
    cherrypy.tree.mount(
        Variables(), '/api/variables',
        {'/':
            {'request.dispatch': cherrypy.dispatch.MethodDispatcher()}
        }
    )
    cherrypy.tree.mount(
        Sources(), '/api/sources',
        {'/':
            {'request.dispatch': cherrypy.dispatch.MethodDispatcher()}
        }
    )
    cherrypy.tree.mount(
        Timeslices(), '/api/timeslices',
        {'/':
            {'request.dispatch': cherrypy.dispatch.MethodDispatcher()}
        }
    )
    cherrypy.tree.mount(
        Root(), '/api',
        {'/':
            {'request.dispatch': cherrypy.dispatch.MethodDispatcher()}
        }
    )
    cherrypy.tree.mount(
        Index(), '/index',
        {'/':
            {'request.dispatch': cherrypy.dispatch.MethodDispatcher()}
        }
    )
    cherrypy.tree.mount(
        Map(), '/map',
        {'/':
            {'request.dispatch': cherrypy.dispatch.MethodDispatcher()}
        }
    )
    cherrypy.tree.mount(
        NeotomaSearch(), '/neotomaQuery',
        {'/':
            {'request.dispatch': cherrypy.dispatch.MethodDispatcher()}
        }
    )
    cherrypy.tree.mount(
        GraphView(), '/graph',
        {'/':
            {'request.dispatch': cherrypy.dispatch.MethodDispatcher()}
        }
    )

    cherrypy.engine.start()
    cherrypy.engine.block()