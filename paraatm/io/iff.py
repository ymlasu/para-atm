"""Functions for reading Integrated Flight Format (IFF) files"""

import pandas as pd
import numpy as np
from pkg_resources import parse_version
import geopandas as gpd
from shapely.geometry import Point

def read_iff_file(filename, record_types=3, callsigns=None, chunksize=50000, encoding='latin-1'):
    """
    Read IFF file and return data frames for requested record types
    
    From IFF 2.15 specification, record types include:

    2. header
    3. track point
    4. flight plan
    5. data source program
    6. sectorization
    7. minimum safe altitude
    8. flight progress
    9. aircraft state

    Parameters
    ----------
    filename : str
        File to read
    record_types : int, sequence of ints, or 'all'
        Record types to return
    callsigns : None, string, or list of strings
        If None, return records for all aircraft callsigns.
        Otherwise, only return records that match the given callsign
        (in the case of a single string) or match one of the specified
        callsigns (in the case of a list of strings).
    chunksize: int
        Number of rows that are read at a time by pd.read_csv.  This
        limits memory usage when working with large files, as we can
        extract out the desired rows from each chunk, isntead of
        reading everything into one large DataFrame and then taking a
        subset.
    encoding: str
        Encoding argument passed on to open and pd.read_csv.  Using
        'latin-1' instead of the default will suppress errors that
        might otherwise occur with minor data corruption.  See
        http://python-notes.curiousefficiency.org/en/latest/python3/text_file_processing.html
    
    Returns
    -------
    DataFrame or dict of DataFrames
       If record_types is a scalar, return a DataFrame containing the
       data for that record type only.  Otherwise, return a dictionary
       mapping each requested record type to a corresponding DataFrame.
    """
    # Note default record_type of 3 (track point) is used for
    # consistency with the behavior of other functions that expect
    # flight tracking data

    # Determine file format version.  This is in record type 1, which
    # for now we assume to occur on the first line.
    with open(filename, 'r') as f:
        version = parse_version(f.readline().split(',')[2])

    # Columns for each record type, from version 2.6 specification.
    cols = {0:['recType','comment'],
            1:['recType','fileType','fileFormatVersion'],
            2:['recType','recTime','fltKey','bcnCode','cid','Source','msgType','AcId','recTypeCat','acType','Orig','Dest','opsType','estOrig','estDest'],
            3:['recType','recTime','fltKey','bcnCode','cid','Source','msgType','AcId','recTypeCat','coord1','coord2','alt','significance','coord1Accur','coord2Accur','altAccur','groundSpeed','course','rateOfClimb','altQualifier','altIndicator','trackPtStatus','leaderDir','scratchPad','msawInhibitInd','assignedAltString','controllingFac','controllingSeg','receivingFac','receivingSec','activeContr','primaryContr','kybrdSubset','kybrdSymbol','adsCode','opsType','airportCode'],
            4:['recType','recTime','fltKey','bcnCode','cid','Source','msgType','AcId','recTypeCat','acType','Orig','Dest','altcode','alt','maxAlt','assignedAltString','requestedAltString','route','estTime','fltCat','perfCat','opsType','equipList','coordinationTime','coordinationTimeType','leaderDir','scratchPad1','scratchPad2','fixPairScratchPad','prefDepArrRoute','prefDepRoute','prefArrRoute'],
            5:['recType','dataSource','programName','programVersion'],
            6:['recType','recTime','Source','msgType','rectypeCat','sectorizationString'],
            7:['recType','recTime','fltKey','bcnCode','cid','Source','msgType','AcId','recTypeCat','coord1','coord2','alt','significance','coord1Accur','coord2Accur','altAccur','msawtype','msawTimeCat','msawLocCat','msawMinSafeAlt','msawIndex1','msawIndex2','msawVolID'],
            8:['recType','recTime','fltKey','bcnCode','cid','Source','msgType','AcId','recTypeCat','acType','Orig','Dest','depTime','depTimeType','arrTime','arrTimeType'],
            9:['recType','recTime','fltKey','bcnCode','cid','Source','msgType','AcId','recTypeCat','coord1','coord2','alt','pitchAngle','trueHeading','rollAngle','trueAirSpeed','fltPhaseIndicator'],
            10:['recType','recTime','fltKey','bcnCode','cid','Source','msgType','AcId','recTypeCat','configType','configSpec']}

    # For newer versions, additional columns are supported.  However,
    # this code could be commented out, and it should still be
    # compatible with newer versions, but just ignoring the additional
    # columns.
    if version >= parse_version('2.13'):
        cols[2] += ['modeSCode']
        cols[3] += ['trackNumber','tptReturnType','modeSCode']
        cols[4] += ['coordinationPoint','coordinationPointType','trackNumber','modeSCode']
    if version >= parse_version('2.15'):
        cols[3] += ['sensorTrackNumberList','spi','dvs','dupM3a','tid']

    # Determine the record type of each row
    with open(filename, 'r', encoding=encoding) as f:
        # An alternative, using less memory, would be to directly
        # create skiprows indices for a particular record type, using
        # a comprehension on enumerate(f); however, that would not
        # allow handling multiple record types.
        line_record_types = [int(line.split(',')[0]) for line in f]

    # Determine which record types to retrieve, and whether the result
    # should be a scalar or dict:
    if record_types == 'all':
        record_types = np.unique(line_record_types)
        scalar_result = False
    elif hasattr(record_types, '__getitem__'):
        scalar_result = False
    else:
        record_types = [record_types]
        scalar_result = True

    if callsigns is not None:
        callsigns = list(np.atleast_1d(callsigns))


    data_frames = dict()
    for record_type in record_types:
        # Construct list of rows to skip:
        skiprows = [i for i,lr in enumerate(line_record_types) if lr != record_type]
        
        # Passing usecols is necessary because for some records, the
        # actual data has extraneous empty columns at the end, in which
        # case the data does not seem to get read correctly without
        # usecols
        if callsigns is None:
            df = pd.concat((chunk for chunk in pd.read_csv(filename, header=None, skiprows=skiprows, names=cols[record_type], usecols=cols[record_type], na_values='?', encoding=encoding, chunksize=chunksize, low_memory=False)), ignore_index=True)
        else:
            df = pd.concat((chunk[chunk['AcId'].isin(callsigns)] for chunk in pd.read_csv(filename, header=None, skiprows=skiprows, names=cols[record_type], usecols=cols[record_type], na_values='?', encoding=encoding, chunksize=chunksize, low_memory=False)), ignore_index=True)

        # For consistency with other PARA-ATM data:
        df.rename(columns={'recTime':'time',
                           'AcId':'callsign',
                           'coord1':'latitude',
                           'coord2':'longitude',
                           'alt':'altitude',
                           'rateOfClimb':'rocd',
                           'groundSpeed':'tas',
                           'course':'heading'},
                  inplace=True)

        if 'time' in df:
            df['time'] = pd.to_datetime(df['time'], unit='s')
        if 'altitude' in df:
            df['altitude'] *= 100 # Convert 100s ft to ft

        # Store to dict of data frames
        data_frames[record_type] = df

    if scalar_result:
        result = data_frames[record_types[0]]
    else:
        result = data_frames

    return result

def read_iff_file_as_gpd(filename, record_types=3, callsigns=None, chunksize=50000, encoding='latin-1'):
    """
    Read IFF file and return data frames for requested record types
    
    From IFF 2.15 specification, record types include:

    2. header
    3. track point
    4. flight plan
    5. data source program
    6. sectorization
    7. minimum safe altitude
    8. flight progress
    9. aircraft state

    Parameters
    ----------
    filename : str
        File to read
    record_types : int, sequence of ints, or 'all'
        Record types to return
    callsigns : None, string, or list of strings
        If None, return records for all aircraft callsigns.
        Otherwise, only return records that match the given callsign
        (in the case of a single string) or match one of the specified
        callsigns (in the case of a list of strings).
    chunksize: int
        Number of rows that are read at a time by pd.read_csv.  This
        limits memory usage when working with large files, as we can
        extract out the desired rows from each chunk, isntead of
        reading everything into one large DataFrame and then taking a
        subset.
    encoding: str
        Encoding argument passed on to open and pd.read_csv.  Using
        'latin-1' instead of the default will suppress errors that
        might otherwise occur with minor data corruption.  See
        http://python-notes.curiousefficiency.org/en/latest/python3/text_file_processing.html
    
    Returns
    -------
    GeoDataFrame or dict or a mix of GeoDataFrames and DataFrames
       If record_types is a scalar and either 3,7 or 9, return a GeoDataFrame
       containing the data for that record type only.  Otherwise, return a dictionary
       mapping each requested record type to a corresponding DataFrame or GeoDataFrame.
    """

    #Run read_iff_file to convert to pandas DataFrame
    result = read_iff_file(filename,record_types=record_types,callsigns=callsigns,chunksize=chunksize,encoding=encoding)

    rec_types_to_convert = [3,7,9]
    
    if not hasattr(record_types, '__getitem__'):
        if record_types in rec_types_to_convert:
            geom = [Point(x,y,z) for x,y,z in zip(result.longitude.values,result.latitude.values,result.altitude.values)]
            result.drop(['latitude','longitude','altitude'], axis=1,inplace=True)
            gdf = gpd.GeoDataFrame(result, geometry=geom)
            gdf.set_crs(epsg=4326,inplace=True)
            result = gdf
    
    if hasattr(record_types, '__getitem__'):
        for key in result.keys():
            if key in rec_types_to_convert:
                df = result[key]
                geom = [Point(x,y,z) for x,y,z in zip(df.longitude.values,df.latitude.values,df.altitude.values)]
                df.drop(['latitude','longitude','altitude'], axis=1,inplace=True)
                gdf = gpd.GeoDataFrame(df, geometry=geom)
                gdf.set_crs(epsg=4326,inplace=True)
                result[key] = gdf

    return result

class IFFSpark:
    def __init__(self):
        from pyspark.sql import SparkSession
        from sedona.register import SedonaRegistrator
        from sedona.utils import SedonaKryoRegistrator, KryoSerializer

        sparkSession = SparkSession.\
            builder.\
            master("local[*]").\
            appName("Sector_IFF_Parser").\
            config("spark.serializer", KryoSerializer.getName).\
            config("spark.kryo.registrator", SedonaKryoRegistrator.getName) .\
            config('spark.jars.packages',
            'org.apache.sedona:sedona-python-adapter-3.0_2.12:1.1.1-incubating,'
            'org.datasyslab:geotools-wrapper:1.1.0-25.2'). \
            getOrCreate()

        SedonaRegistrator.registerAll(sparkSession)
        self.sparkSession = sparkSession

    def register_iff_file_as_sql_table(self,filename, record_types=3, callsigns=None, chunksize=50000, encoding='latin-1',query_name=None):
        from sedona.register import SedonaRegistrator
        from pyspark.sql.types import IntegerType

        SedonaRegistrator.registerAll(self.sparkSession)

        iff_schema = self.iff_schema()
        df = self.sparkSession.read.csv(filename, header=False, sep=",", schema=iff_schema)    
        
        cols = ['recType', 'recTime', 'acId', 'lat', 'lon', 'alt']
        df = df.select(*cols).filter(df['recType']==3).withColumn("recTime", df['recTime'].cast(IntegerType()))
        
        if query_name is not None:
            df.registerTempTable(query_name)
        
        return df.toPandas()

    def convert_position_to_geometry(self,tablename,register_name=None):
        df=self.sparkSession.sql(
            """
            SELECT *,
            ST_Point(CAST(lat AS Decimal(24, 20)), CAST(lon AS Decimal(24, 20))) AS geom
            FROM {}
            """.format(tablename))

        if register_name is not None:
            df.createOrReplaceTempView(register_name)
        
        return gpd.GeoDataFrame(df.toPandas(),geometry='geom',crs='EPSG:4326')


    def query_time(self, tablename,t_start,t_end,register_name=None):
        df = self.sparkSession.sql(
            """
            SELECT *
            FROM {}
            WHERE recTime>={} AND recTime<={}
            """.format(tablename,t_start, t_end))


        if register_name is not None:
            df.createOrReplaceTempView(register_name)
        
        return gpd.GeoDataFrame(df.toPandas(),geometry='geom',crs='EPSG:4326')

    def query_fix_and_radius(self, tablename,fix_x_y_z,radius,vertical_thresh,register_name=None):
        df = self.sparkSession.sql(
            """
                SELECT *
                FROM {}
                WHERE ST_Contains(ST_PolygonFromEnvelope({}, {}, {}, {}), geom) AND alt>{}
            """.format(tablename,fix_x_y_z[0]-radius, fix_x_y_z[1]-radius, fix_x_y_z[0]+radius,fix_x_y_z[1]+radius,fix_x_y_z[2]+vertical_thresh))
        
        if register_name is not None:
            df.createOrReplaceTempView(register_name)

        return gpd.GeoDataFrame(df.toPandas(),geometry='geom',crs='EPSG:4326')
            

    #Create load_schema function that returns variable 'myschema' specifically for IFF recType=3.
    def iff_schema(self):
        from pyspark.sql.types import (ShortType, StringType, StructType,StructField,LongType, IntegerType, DoubleType)
        myschema = StructType([
            StructField("recType", ShortType(), True),  # 1  //track point record type number
            StructField("recTime", StringType(), True),  # 2  //seconds since midnigght 1/1/70 UTC
            StructField("fltKey", LongType(), True),  # 3  //flight key
            StructField("bcnCode", IntegerType(), True),  # 4  //digit range from 0 to 7
            StructField("cid", IntegerType(), True),  # 5  //computer flight id
            StructField("Source", StringType(), True),  # 6  //source of the record
            StructField("msgType", StringType(), True),  # 7
            StructField("acId", StringType(), True),  # 8  //call sign
            StructField("recTypeCat", IntegerType(), True),  # 9
            StructField("lat", DoubleType(), True),  # 10
            StructField("lon", DoubleType(), True),  # 11
            StructField("alt", DoubleType(), True),  # 12  //in 100s of feet
            StructField("significance", ShortType(), True),  # 13 //digit range from 1 to 10
            StructField("latAcc", DoubleType(), True),  # 14
            StructField("lonAcc", DoubleType(), True),  # 15
            StructField("altAcc", DoubleType(), True),  # 16
            StructField("groundSpeed", IntegerType(), True),  # 17 //in knots
            StructField("course", DoubleType(), True),  # 18  //in degrees from true north
            StructField("rateOfClimb", DoubleType(), True),  # 19  //in feet per minute
            StructField("altQualifier", StringType(), True),  # 20  //Altitude qualifier (the “B4 character”)
            StructField("altIndicator", StringType(), True),  # 21  //Altitude indicator (the “C4 character”)
            StructField("trackPtStatus", StringType(), True),  # 22  //Track point status (e.g., ‘C’ for coast)
            StructField("leaderDir", IntegerType(), True),  # 23  //int 0-8 representing the direction of the leader line
            StructField("scratchPad", StringType(), True),  # 24
            StructField("msawInhibitInd", ShortType(), True),  # 25 // MSAW Inhibit Indicator (0=not inhibited, 1=inhibited)
            StructField("assignedAltString", StringType(), True),  # 26
            StructField("controllingFac", StringType(), True),  # 27
            StructField("controllingSec", StringType(), True),  # 28
            StructField("receivingFac", StringType(), True),  # 29
            StructField("receivingSec", StringType(), True),  # 30
            StructField("activeContr", IntegerType(), True),  # 31  // the active control number
            StructField("primaryContr", IntegerType(), True),
            # 32  //The primary(previous, controlling, or possible next)controller number
            StructField("kybrdSubset", StringType(), True),  # 33  //identifies a subset of controller keyboards
            StructField("kybrdSymbol", StringType(), True),  # 34  //identifies a keyboard within the keyboard subsets
            StructField("adsCode", IntegerType(), True),  # 35  //arrival departure status code
            StructField("opsType", StringType(), True),  # 36  //Operations type (O/E/A/D/I/U)from ARTS and ARTS 3A data
            StructField("airportCode", StringType(), True),  # 37
            StructField("trackNumber", IntegerType(), True),  # 38
            StructField("tptReturnType", StringType(), True),  # 39
            StructField("modeSCode", StringType(), True)  # 40
        ])
        return myschema
