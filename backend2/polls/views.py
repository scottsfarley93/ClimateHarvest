from django.http import HttpResponse
import json


def getConnection(host, username, password, database):
    """Connect to database and return the connection cursor to allow insertion"""
    import psycopg2
    try:
        connectString = "dbname='" + str(database) + "' user='" + str(username) + "' host='" + str(host) + "' password='" + str(password) + "'"
        conn = psycopg2.connect(connectString)
        return conn
    except:
        print "I am unable to connect to the database"
    return

##establish connection
connection = getConnection("localhost", "postgres" , "Sequoia93!", "climateHarvest")


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
        value = results
        return value
    else:
        return False






def index(request):
    r = queryPoint(-118, 37)
    r = json.dumps(r)
    return HttpResponse(r)