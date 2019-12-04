def getTableList(cursor):

    #Execute query to fetch flight data
    query = "SELECT t.table_name \
             FROM information_schema.tables t \
             JOIN information_schema.columns c ON c.table_name = t.table_name \
             WHERE c.column_name LIKE 'callsign'"
    cursor.execute(query)
    results = cursor.fetchall()
    return [result[0] for result in results]
