'''

NASA NextGen NAS ULI Information Fusion
        
@organization: PARA Lab, Arizona State University (PI Dr. Yongming Liu)
@author: Hari Iyer
@date: 01/19/2018

MapView wraps the map to be displayed on the application UI.

'''

'''
    buildMap() returns the map to be rendered onto the application layout, with all the map features and functions 
    embedded according to user request.
'''

from PARA_ATM import *

def buildMap(flightSelected, dateRangeSelected, filterToggles, cursor, commandParameters):

    #Data container definitions
    flightResults = []
    waypointResults = []
    airportResults = []
    waypointLocations = []
    commandName = ""
    commandArguments = []
    airportFilterResults = []
    source = []
    destination = []
    sourceIATA = ""
    destinationIATA = ""
    
    #Load toggle values as per user selection
    airportToggle = int(filterToggles[0])
    waypointToggle = int(filterToggles[1])
    weatherToggle = int(filterToggles[2])
    sectorToggle = int(filterToggles[3])
   
    #Resources directory
    resourcesDir = str(Path(__file__).parent.parent.parent.parent) + "/resources/"
    
    #Get command name and parameter if any
    def tdds_data():
        """
            process results from the TDDS command

            returns:
                    flightResults = 3d list of shape (# pts in flight, # flights, 4)
                                    last 4 elements are UTC time, smes status, callsign, position (lat,lon)
                    source        = airport to focus on
                    destination   = same as source
        """
        flightResults = []
        commandName = commandParameters[0]
        #TDDS returns tuple (dataframe, airport IATA)
        commandArguments = commandParameters[1:]
        tdds_data = commandArguments[0]
        airport = commandArguments[1]
        #get position of airport
        cursor.execute("SELECT latitude,longitude from airports WHERE iata='%s'"%(airport))
        airportLatLon = cursor.fetchall()
        #need this to zoom the map
        source = [airport,airportLatLon[0][0],airportLatLon[0][1]]
        destination = source
        
        #iterate through each tdds message
        for index,row in tdds_data.iterrows():
            lookahead=row['velocity']*.01
            flightResults.append([[str(row['time']),str(row['status']),row['callsign'],str(row['latitude'])+','+str(row['longitude']),str(lookahead)]])
        
        return flightResults,source,destination

    def NATS_data():
        """
            process the NATS simulation output

            returns:
                    flightResults = same as TDDS_data above
                    source        = same as TDDS_data above
                    destination   = destination airport and position
        """
        
        flightResults = []
        commandName = commandParameters[0]
        nats_data = commandParameters[1]
        #select first airport as zoom location
        sourceIATA = nats_data['origin'].iloc[0]
        destIATA = nats_data['destination'].iloc[0]
        cursor.execute("SELECT latitude, longitude from airports WHERE iata = %s", ("" + sourceIATA[1:],))
        airportsLatLon = cursor.fetchall()
        source = [sourceIATA, airportsLatLon[0][0], airportsLatLon[0][1]]
        cursor.execute("SELECT latitude, longitude from airports WHERE iata = %s", ("" + destIATA[1:],))
        airportsLatLon = cursor.fetchall()
        destination = [destIATA, airportsLatLon[0][0], airportsLatLon[0][1]]
        
        #select the distinct aircraft ids
        for acid in np.unique(nats_data['callsign']):
            ac_results = []
            #select all the data relevant to given aircraft
            for index,row in nats_data[nats_data['callsign']==acid].iterrows():
                ac_results.append([str(row['time']),row['mode'],row['callsign'],str(row['lat'])+','+str(row['lon'])])
            flightResults.append(ac_results)
        
        return flightResults,source,destination

    #Get flight, waypoint, and airport data from the database to be used to generate map
    def flight_trajectory():
        """
            process the selection from the dropdown menus
        """        
        cursor.execute("SELECT source, destination from flight_data WHERE callsign = %s", ("" + flightSelected,))
        airportResults = cursor.fetchall()
        sourceIATA = airportResults[0][0]
        destinationIATA = airportResults[0][1]
        if waypointToggle:
            cursor.execute("SELECT waypoints from waypoint_routes WHERE source = %s AND destination = %s", ("" + sourceIATA, "" + destinationIATA,))
            waypointResults = cursor.fetchall()
            for waypoint in waypointResults[0][0].split(","):
                cursor.execute("SELECT latitude, longitude from waypoint_locations WHERE waypoint = %s", ("" + waypoint,))
                waypointLocation = cursor.fetchall()[0]
                waypointLocations.append([waypoint, waypointLocation[0], waypointLocation[1]])
        cursor.execute("SELECT latitude, longitude from airports WHERE iata = %s", ("" + sourceIATA,))
        airportsLatLon = cursor.fetchall()
        source = [sourceIATA, airportsLatLon[0][0], airportsLatLon[0][1]]
        cursor.execute("SELECT latitude, longitude from airports WHERE iata = %s", ("" + destinationIATA,))
        airportsLatLon = cursor.fetchall()
        destination = [destinationIATA, airportsLatLon[0][0], airportsLatLon[0][1]]
        for date in dateRangeSelected:
            cursor.execute("SELECT * from flight_data WHERE callsign = %s AND utc LIKE %s", ("" + flightSelected, "" + (date + '%'),))
            flightDailyResults = cursor.fetchall()
            flightResults.append([list(flightData) for flightData in flightDailyResults if list(flightData)])
        if airportToggle:
            cursor.execute("SELECT * from airports")
            airportData = cursor.fetchall()
            for airport in airportData:
                airportFilterResults.append(list(airport))
        return airportResults,sourceIATA,destinationIATA,airportsLatLon,source,destination,flightResults


    #commands which call init_map all pass through this code block
    #so sequence through each potential caller
    try:
        flightResults,source,destination = tdds_data()
    except Exception as t:
        try:
            airportResults,sourceIATA,destinationIATA,airportsLatLon,source,destination,flightResults = flight_trajectory()
        except Exception as f:
            try:
                flightResults,source,destination = NATS_data()
            except Exception as v:
                pass
    
    #build the html to display in the GUI
    #documentation for leaflet https://leafletjs.com/index.html
    try:
        html = '''
        <!DOCTYPE html>
           <head>
              <title>Full Screen Leaflet Map</title>
              <meta charset="utf-8" />
              <link 
                 rel="stylesheet" 
                 href="https://unpkg.com/leaflet@1.2.0/dist/leaflet.css"
                 />
              <style>
                 .popupCustom .leaflet-popup-tip,
                 .popupCustom .leaflet-popup-content-wrapper {
                  background: #e0e0e0;
                  color: #234c5e;
                  opacity: 0.8;
                  }
                 body {
                 padding: 0;
                 margin: 0;
                 }
                 html, body, #map {
                 height: 100%;
                 width: 100%;
                 }
              </style>
           </head>
           <body>
              <div id="map"></div>
              <script src="https://unpkg.com/leaflet@1.2.0/dist/leaflet.js"></script>
              <script type="text/javascript" src="https://raw.githubusercontent.com/openplans/Leaflet.AnimatedMarker/master/src/AnimatedMarker.js"></script>
              <script src="https://raw.githubusercontent.com/Leaflet/Leaflet.heat/gh-pages/dist/leaflet-heat.js"></script>
              <script src="https://raw.githubusercontent.com/aerisweather/aerismaps-visualizer/master/aerismaps-visualizer.min.js"></script>
               <script src="https://unpkg.com/esri-leaflet@2.1.3/dist/esri-leaflet.js"
                integrity="sha512-pijLQd2FbV/7+Jwa86Mk3ACxnasfIMzJRrIlVQsuPKPCfUBCDMDUoLiBQRg7dAQY6D1rkmCcR8286hVTn/wlIg=="
                crossorigin=""></script>
              <script>
                 
                 var flightPaths = ''' + repr(flightResults) + ''';
                 var source = ''' + repr(source) + ''';
                 var weatherToggle = ''' + repr(weatherToggle) + ''';
                 var waypoints = ''' + repr(waypointLocations) + ''';
                 var destination = ''' + repr(destination) + ''';
                 var sector = ''' + repr(sectorToggle) + ''';
                 var airportResults = ''' + repr(airportFilterResults) + ''';
                 var commandName = ''' + repr(commandName) + ''';
                 var commandArguments = ''' + repr(commandArguments) + ''';
                 var resourcesDir = ''' + repr(resourcesDir) + ''';
                 
                 <!-- Center map on the U.S. -->
                 var map = L.map('map').setView([38.04, -99.17], 5);
                 var mapLink = '< a href="http://openstreetmap.org">OpenStreetMap</a>';
                 L.tileLayer('http://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
                              maxZoom: 18,
                              attribution: 'Map data <a href="http://openstreetmap.org">OpenStreetMap</a> contributors, ' +
                                  '<a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, ' +
                                  'Imagery  <a href="http://mapbox.com">Mapbox</a>',
                              id: 'mapbox.streets'
                          }).addTo(map);
                 
                 <!-- PARA-ATM logo -->
                 L.Control.Watermark = L.Control.extend({
                    onAdd: function(map) {
                        var img = L.DomUtil.create('img');
                        
                        img.src = 'https://i.imgur.com/5EqaE4e.png';
                        img.style.width = '200px';
                        
                        return img;
                 }
                 });
                 L.control.watermark = function(opts) {
                    return new L.Control.Watermark(opts);
                 }
                 L.control.watermark({ position: 'bottomleft' }).addTo(map);
                  
                 <!-- Markers for points and airports -->
                 var markerIcon = L.icon({iconUrl: 'https://storage.googleapis.com/support-kms-prod/SNP_2752063_en_v0'});
                 var airportIcon = L.icon({iconUrl: 'https://storage.googleapis.com/support-kms-prod/SNP_2752068_en_v0'});                  
                                   
                 <!-- Placeholder -->
                 if(commandName == 'Airport')
                 {
                     map.setHtml("LiveFlights.html");
                 }
                
                 trajectories = [];
                 currentTrajectory = [];
                 markers = [];
                 ssds = [];

                 <!-- Cycle through the 3d list we built from command output -->
                 for (var i = 0; i < flightPaths.length; i++) {
                     for (var j = 0; j < flightPaths[i].length; j++) {

                         var flightPosition = flightPaths[i][j][3].split(",");
                         var callsign = flightPaths[i][j][2];
                         var timestamp = flightPaths[i][j][0];

                         var latitude = parseFloat(flightPosition[0]);
                         var longitude = parseFloat(flightPosition[1]);

                         currentTrajectory.push(new L.LatLng(latitude, longitude));
                         
                         var status = flightPaths[i][j][1]

                         <!-- Build SSD for phase of flight -->
                         if(status=='onsurface')
                         {
                            var ssd = L.circle([latitude,longitude], {radius: 15, opacity: 0.5});
                            ssds.push(ssd);
                         }

                         else if(status=='onramp')
                         {
                            var ssd = L.circle([latitude,longitude], {radius: 45, opacity: 0.5});
                            ssds.push(ssd);
                         }

                         else if(status=='airborne')
                         {
                            var ssd = L.circle([latitude,longitude], {radius: 800, opacity: 0.5});
                            ssds.push(ssd);
                         }

                         <!-- Mark each aircraft -->
                         var marker = L.marker([latitude, longitude], {icon: markerIcon}).addTo(map).bindPopup("" + timestamp + " " + callsign + ": " + latitude + ", " + longitude, {closeOnClick: false, autoClose: false});

                         markers.push(marker);
                     
                     } 
                     
                     trajectories.push(currentTrajectory);
                     currentTrajectory = [];
                 }   
                 
                 <!-- Display airport locations -->
                 if(airportResults.length > 0)
                 {
                     for(var airport = 0; airport < airportResults.length; airport++)
                     {
                         var airportCode = airportResults[airport][0];
                         var airportLatitude = parseFloat(airportResults[airport][1]);
                         var airportLongitude = parseFloat(airportResults[airport][2]);
                         var airportName = airportResults[airport][3];
                         var marker = L.marker([airportLatitude, airportLongitude], {icon: airportIcon}).addTo(map).bindPopup(airportCode + ": " + airportName, {closeOnClick: false, autoClose: false});
                     }
                 
                 }
                 
                 <!-- Sector layer -->
                 if(sector == 1)
                 {
                 
                     L.esri.tiledMapLayer({
                        url: "https://services.arcgisonline.com/ArcGIS/rest/services/Specialty/World_Navigation_Charts/MapServer",
                        detectRetina: false,
                        minZoom: 3,
                        maxZoom: 10
                      }).addTo(map);
                 
                 }

                 <!-- Show start and end of each flight -->
                 var sourceMarker;
                 var destinationMarker;
                 
                 if(trajectories[0].length > 0) {
                     sourceMarker = L.marker([parseFloat(source[1]), parseFloat(source[2])]).addTo(map).bindPopup(source[0].toString(), {closeOnClick: false, autoClose: false}).openPopup();
                     destinationMarker = L.marker([parseFloat(destination[1]), parseFloat(destination[2])]).addTo(map).bindPopup(destination[0].toString(), {closeOnClick: false, autoClose: false}).openPopup();
                 }
                 
                 <!-- Display SSD circles -->
                 if(ssds.length > 0)
                 {
                    var ssdGroup = new L.featureGroup(ssds).addTo(map);
                 }

                 <!-- Connect points on the flight(s) -->
                 var currentPath = null;
                 var group = new L.featureGroup(markers);
                 for (var trajectory = 0; trajectory < trajectories.length; trajectory++) {
                     currentPath = L.polyline(trajectories[trajectory], {color: '#'+(Math.random()*0xFFFFFF<<0).toString(16)}).addTo(map);
                 }

                 <!-- Weather filter -->
                 if(weatherToggle == 1)
                 {
                 
                     var imageUrl = 'file:///' + resourcesDir + 'weather/20March.gif';
                     var imageBounds = [[6.082180, -120.892187],[48.459884, -63.060156]];
                     L.imageOverlay(imageUrl, imageBounds).addTo(map);
                  
                 }
                 

                 /*
                 if(CUSTOM_COMMAND)
                 {
                 
                     var imageUrl = 'IMAGE_OVERLAY_LOCATION_HERE';
                     var imageBounds = [[], []];    //Image bounds here
                     L.imageOverlay(imageUrl, imageBounds).addTo(map);
                 }
                 */
                 
                 var animatedMarker = null;
                 
                 <!-- Animation pulls from MovingMarker.js -->
                 if(trajectories[0].length > 0)
                 {
                     animatedMarker = L.animatedMarker(currentPath.getLatLngs(), {
                       distance: 3000,
                       interval: 100,
                       autoStart: false
                     }).bindPopup("Click to animate", {closeOnClick: false, autoClose: false});
                     
                     map.addLayer(animatedMarker);
                     animatedMarker.openPopup();
                     animatedMarker.on('click', moveMarker)
                     

                 }
                 
                 <!-- Zoom in on selected airport -->
                 if(source.length>0){
                 map.setView([parseFloat(source[1]), parseFloat(source[2])], 15);
                 }

                 <!-- On click, animate flight path -->
                 function moveMarker()
                 {
                     animatedMarker.start();
                 }
                 
                 <!-- Waypoint display -->
                 if(waypoints.length > 0) {
                     for (var waypoint = 0; waypoint < waypoints.length; waypoint++) {
                         waypointMarker = L.marker([parseFloat(waypoints[waypoint][1]), parseFloat(waypoints[waypoint][2])]).addTo(map).bindPopup(waypoints[waypoint][0].toString(), {closeOnClick: false, autoClose: false}).openPopup();
                     }
                 }
                 
            </script>
           </body>
        </html>

        '''
        #debugging
        f=open('vis_test.html','w')
        f.write(html)
        f.close()
    except Exception as e:
        pass
    return html
