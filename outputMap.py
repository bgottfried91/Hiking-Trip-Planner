'''
Created on May 5, 2016

@author: Brian
'''
import datetime
from lxml import etree
from Utils import addTime
from Itinerary import Itinerary
import googlemaps
import webbrowser
import sys

def createMap(xmlObj,outputFile,display):
    optimal_route = getMapListFromXML(xmlObj)
    
    Page_1 = """
    <!DOCTYPE html>
    <html lang="en">
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="initial-scale=1.0, user-scalable=no">
        <meta name="description" content="Randy Olson uses machine learning to find the optimal road trip across the U.S.">
        <meta name="author" content="Randal S. Olson">
        
        <title>The optimal road trip across the U.S. according to machine learning</title>
        <style>
          html, body, #map-canvas {
            height: 100%;
            margin: 0px;
            padding: 0px
          }
          #panel {
            position: absolute;
            top: 5px;
            left: 50%;
            margin-left: -180px;
            z-index: 5;
            background-color: #fff;
            padding: 10px;
            border: 1px solid #999;
          }
        </style>
        <script src="https://maps.googleapis.com/maps/api/js?v=3.exp&signed_in=true"></script>
        <script>
            var routes_list = []
            var markerOptions = {icon: "http://maps.gstatic.com/mapfiles/markers2/marker.png"};
            var directionsDisplayOptions = {preserveViewport: true,
                                            markerOptions: markerOptions};
            var directionsService = new google.maps.DirectionsService();
            var map;
            function initialize() {
              var center = new google.maps.LatLng(39, -96);
              var mapOptions = {
                zoom: 5,
                center: center
              };
              map = new google.maps.Map(document.getElementById('map-canvas'), mapOptions);
              for (i=0; i<routes_list.length; i++) {
                routes_list[i].setMap(map); 
              }
            }
            function calcRoute(start, end, routes) {
              
              var directionsDisplay = new google.maps.DirectionsRenderer(directionsDisplayOptions);
              var waypts = [];
              for (var i = 0; i < routes.length; i++) {
                waypts.push({
                  location:routes[i],
                  stopover:true});
                }
              
              var request = {
                  origin: start,
                  destination: end,
                  waypoints: waypts,
                  optimizeWaypoints: false,
                  travelMode: google.maps.TravelMode.DRIVING
              };
              directionsService.route(request, function(response, status) {
                if (status == google.maps.DirectionsStatus.OK) {
                    directionsDisplay.setDirections(response);      
                }
              });
              routes_list.push(directionsDisplay);
            }
            function createRoutes(route) {
                // Google's free map API is limited to 10 waypoints so need to break into batches
                var subset = 0;
                while (subset < route.length) {
                    var waypointSubset = route.slice(subset, subset + 10);
                    var startPoint = waypointSubset[0];
                    var midPoints = waypointSubset.slice(1, waypointSubset.length - 1);
                    var endPoint = waypointSubset[waypointSubset.length - 1];
                    calcRoute(startPoint, endPoint, midPoints);
                    subset += 9;
                }
            }
    """
    Page_2 = """
            
            createRoutes(optimal_route);
            google.maps.event.addDomListener(window, 'load', initialize);
        </script>
      </head>
      <body>
        <div id="map-canvas"></div>
      </body>
    </html>
    """

    with open(outputFile, 'w') as fs:
        fs.write(Page_1)
        fs.write("\t\t\toptimal_route = {0}".format(str(optimal_route)))
        fs.write(Page_2)

    if display:
        webbrowser.open_new_tab(outputFile)
        

def getMapListFromXML(xmlObj):
    mapList=[]
    mapList.append(xmlObj.find("start_location").text)  #First, add starting location
    for location in xmlObj.findall("location"):
        mapList.append(location.find("trailhead").text)
    mapList.append(xmlObj.find("end_location").text)
    return mapList

if __name__ == '__main__':
    xmlFile=sys.argv[1]
    xmlObj=etree.parse(xmlFile)
    createMap(xmlObj, sys.argv[2], 1)
