from paraatm.Commands.Helpers import DataStore

def getTableList(cursor):

    #Execute query to fetch flight data
    query = "SELECT t.table_name \
             FROM information_schema.tables t \
             JOIN information_schema.columns c ON c.table_name = t.table_name \
             WHERE c.column_name LIKE 'callsign'"
    cursor.execute(query)
    results = cursor.fetchall()
    return [result[0] for result in results]

def checkForTable(filename):

    db_access = DataStore.Access()
    if not db_access.tableExists(filename):
        # Hacky way to indicate table doesn't exist
        raise DataStore.dbError
    
    try:
        return db_access.getNATSdata(filename)[1]
    except DataStore.dbError:
        db_access.connection.rollback()
        try:
            return db_access.getIFFdata(filename)[1]
        except DataStore.dbError:
            return db_access.getSMESdata(filename)[1]
