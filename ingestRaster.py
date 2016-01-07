import os
import subprocess

os.environ['PATH'] += os.pathsep + "/Library/postgresql/9.4/bin"

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

def ingest(connection, rasterOnDisk, dataSource,  varName, varCode, tileX, tileY):
    tableName = dataSource + "_" + varName + "_" + str(tileX) + "x" + str(tileY)
    print "Table name is: " , tableName
    ##prepare sql
    ##This sql goes into the vars table so we can lookup the raster table later
    ##Metadata
    sql = 'INSERT INTO public.vars("varID", "dataSource", "variableCode", "variableName", "tileX", "tileY", "tableName", modified)'
    sql += " VALUES (DEFAULT, '" + str(dataSource) + "', " + str(varCode) + ", '" + str(varName) + "', " + str(tileX) + ", "
    sql += str(tileY) + ", '"  + str(tableName) + "', Default);"
    print "Executing SQL: " , sql
    cursor = connection.cursor()
    cursor.execute(sql)
    connection.commit()
    print "Insertion complete."
    cursor.execute("SELECT COUNT(*) FROM public.vars")
    rows = cursor.fetchall()
    print "New number of rows is: " , rows[0][0]

    ##now create a new table with the raster
    command = "raster2pgsql -s 4326" ##wgs 1984
    command += " -d" ## drop if a table already exists with this name
    command += " -I" ##spatial index
    command += " -C " ##enforce constraints
    #command += " -M " ##vaccuum analyze
    command += rasterOnDisk
    command += " -t "  + str(tileX) + "x" + str(tileY)  + " " ##pixels per tile
    command += tableName
    print "Running command: " , command
    sql = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    (out, err) = sql.communicate()
    print "Got SQL from system call. Now inserting."
    cursor.execute(out)
    #print "Executed raster ingest. Tidying up."
    #cursor.execute("VACUUM FULL;")
    connection.commit()
    print "Done."

#ingest(connection, "/Users/scottsfarley/downloads/alt_10m_bil/alt.bil", "WorldClim", "Altitude", -1, 100, 100)

for i in range(1, 20):
    rName = "/Users/scottsfarley/downloads/bio_10m_bil/bio" + str(i) + ".bil"
    varName = "BioClim" + str(i)
    ingest(connection, rName, "WorldClim", varName, -1, 100, 100)
