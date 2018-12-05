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
    try:
        commandName = commandParameters[0]
        commandArguments = commandParameters[1]
        print(len(list(commandArguments['latitude'])))
        position = [str(commandArguments['latitude'][i])+','+str(commandArguments['longitude'][i]) for i in range(len(list(commandArguments['latitude'])))]
        print(position[0])
        flightResults.append([],list(commandArguments['time']),list(commandArguments['callsign']),position)
        print(flightResults)

    except:
        
        pass
    
    #Get flight, waypoint, and airport data from the database to be used to generate map
    try:
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
            
    except:
        pass
    
    
    #Generate the map HTML and return to main application call
    return '''      
          
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
                 var map = L.map('map').setView([38.04, -99.17], 5);
                 var mapLink = '< a href="http://openstreetmap.org">OpenStreetMap</a>';
                 L.tileLayer('http://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
                              maxZoom: 18,
                              attribution: 'Map data <a href="http://openstreetmap.org">OpenStreetMap</a> contributors, ' +
                                  '<a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, ' +
                                  'Imagery  <a href="http://mapbox.com">Mapbox</a>',
                              id: 'mapbox.streets'
                          }).addTo(map);
                  
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
                  
                  
                 var markerIcon = L.icon({iconUrl: 'https://storage.googleapis.com/support-kms-prod/SNP_2752063_en_v0'});
                 var airportIcon = L.icon({iconUrl: 'https://storage.googleapis.com/support-kms-prod/SNP_2752068_en_v0'});                  
                                   
                 if(commandName == 'airport')
                 {
                     map.setHtml("LiveFlights.html");
                 }
                
                 trajectories = [];
                 currentTrajectory = [];
                 markers = [];

                 for (var i = 0; i < flightPaths.length; i++) {
                     for (var j = 0; j < flightPaths[i].length; j++) {
                     
                         var flightPosition = flightPaths[i][3][j].split(",");
                         
                         var latitude = parseFloat(flightPosition[0]);
                         var longitude = parseFloat(flightPosition[1]);
                         
                         currentTrajectory.push(new L.LatLng(latitude, longitude));
                         
                         var marker = L.marker([latitude, longitude], {icon: markerIcon}).addTo(map).bindPopup("" + latitude + ", " + longitude, {closeOnClick: false, autoClose: false});
                         markers.push(marker);
                     
                     } 
                     
                     trajectories.push(currentTrajectory);
                     currentTrajectory = [];
                 }   
                 
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
                 
                 if(sector == 1)
                 {
                 
                     L.esri.tiledMapLayer({
                        url: "https://services.arcgisonline.com/ArcGIS/rest/services/Specialty/World_Navigation_Charts/MapServer",
                        detectRetina: false,
                        minZoom: 3,
                        maxZoom: 10
                      }).addTo(map);
                 
                 }
                 var sourceMarker;
                 var destinationMarker;
                 
                 if(trajectories[0].length > 0) {
                     sourceMarker = L.marker([parseFloat(source[1]), parseFloat(source[2])]).addTo(map).bindPopup(source[0].toString(), {closeOnClick: false, autoClose: false}).openPopup();
                     destinationMarker = L.marker([parseFloat(destination[1]), parseFloat(destination[2])]).addTo(map).bindPopup(destination[0].toString(), {closeOnClick: false, autoClose: false}).openPopup();
                 }
                 var currentPath = null;
                 var group = new L.featureGroup(markers);
                 for (var trajectory = 0; trajectory < trajectories.length; trajectory++) {
                     currentPath = L.polyline(trajectories[trajectory], {color: '#'+(Math.random()*0xFFFFFF<<0).toString(16)}).addTo(map);
                 }
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
                 
                 map.setView([parseFloat(source[1]), parseFloat(source[2])], 15);

                 function moveMarker()
                 {
                     animatedMarker.start();
                 }
                 
                 if(waypoints.length > 0) {
                     for (var waypoint = 0; waypoint < waypoints.length; waypoint++) {
                         waypointMarker = L.marker([parseFloat(waypoints[waypoint][1]), parseFloat(waypoints[waypoint][2])]).addTo(map).bindPopup(waypoints[waypoint][0].toString(), {closeOnClick: false, autoClose: false}).openPopup();
                     }
                 }
                 
            </script>
           </body>
        </html>

  '''
