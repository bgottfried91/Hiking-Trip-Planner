# Hiking Trip Planner

This is a route-planning tool for planning a trips visiting hiking locations across the lower 48 United States. It can find the optimal route for a trip based on the starting and ending dates and starting and ending locations, using a database of ~120 different hiking locations. It will automatically optimize for the shortest path (in miles), a day-time high of 80 degrees farenheit (based on NOAA data for weather stations near each hiking location), a trip with the highest number of itineraries (i.e. less time driving and more time hiking) and a trip with no more than 3 empty dates (days without a hiking trip planned). It is based on the route planning algorithm created by [Randal Olson](http://www.randalolson.com/2015/03/08/computing-the-optimal-road-trip-across-the-u-s/) and the single-script implementation of it designed by [Andrew Liesenger](https://github.com/rhiever/Data-Analysis-and-Machine-Learning-Projects/blob/master/optimal-road-trip/OptimalRoadTripHtmlSaveAndDisplay.py).

## Installation

You'll need to install the latest version of Python 2.7 (no guarantees the code will work with Python 3) and several libraries beyond the base Python libraries:

+ googlemaps

+ lxml

+ numpy

+ sqlite3


## Usage

The functional script is GMapsGenetic.py. Running just the base script with no parameters will find the optimal route between all locations in the database, using today as the starting date. There are a variety of optional parameters that can be provided to adjust the behavior:

 | Shortcut                        | Long Version                               | Description                                                   |
 | --------------------------- | ------------------------------------------ | ------------------------------------------------------------- |
 |-h| --help             | show parameter list and descriptions | 
 | -sd STARTDATE| --StartDate STARTDATE | Enter the start date for the trip in the format MM/DD/YY. If not supplied, then today is used. |           
  |-ed ENDDATE| --EndDate ENDDATE|                        Enter the end date for the trip in the format                        MM/DD/YY. If not supplied, then no end date is                        assumed.|
  |-sl STARTLOC| --StartLoc STARTLOC|                        Enter the starting location for the trip in standard                        US address format. If not supplied, then no location                        is assumed.|
 | -el ENDLOC| --EndLoc ENDLOC|                        Enter the ending location for the trip in standard US                        address format. If not supplied, then no location is                        assumed.|
 | -rl RESTRICTEDLOCATIONS| --RestrictedLocations RESTRICTEDLOCATIONS|                        Enter a comma-separated string of itinerary IDs* that                        should be ignored when building the list of locations.                        If none are supplied, all in the database are used.|
  |-mt MORNINGTIME| --MorningTime MORNINGTIME|                        Enter the time before which no driving should be                        considered in 24hr HH:MM:SS format. I.E. if you don't                        want to start driving on any day before 8am, enter                        08:00:00.|
  |-et EVENINGTIME| --EveningTime EVENINGTIME|                        Enter the time after which no driving should be                        considered in 24hr HH:MM:SS format. I.E. if you don't                        want to start driving on any day after 9pm, enter                        21:00:00.|
  |-od OUTPUTDIRECTORY| --OutputDirectory OUTPUTDIRECTORY|                        Enter the file path to which to output the XML file of                        the route.|
                        
  *Itinierary IDs can be found inside the sqlite database hikingData.db, in the ID column of the Itin table.
  
Examples of queries using these parameters:

| Query                                            | Effect |
|------------------------------------------------|---------------------------------------------------------------------------------|
| python GMapsGenetic.py -sd "4/2/2017"| Will find the optimal route between all locations in the database with a start date of 4/2/2017. This start date affects the temperature predictions for each location and thus the route order|
|python GMapsGenetic.py -sd "4/2/2017" "5/1/2017"| Will find the optimal route that starts on 4/2/2017 and ends no later than 5/1/2017|
|python GMapsGenetic.py -sd "4/2/2017" -ed "5/1/2017" -sl "1600 Pennsylvania Ave NW, Washington, DC 20500"| Will find the optimal route that starts on 4/2/2017 from 1600 Pennsylvania Ave and ends no later than 5/1/2017.|
|python GMapsGenetic.py -sd "4/2/2017" -ed "5/1/2017" -sl "Wilmington, NC" -el "Wilmington, NC" -mt "09:00:00" -et "21:00:00" -rl "85,86"| Will find the optimal route starting and ending in Wilmington, NC that begins on 4/2/2017, ends on 5/1/2017, only allows for driving between 9am and 9pm, and ignores hikes in Great Smokey Mountains National Park.

## Contributing

1. Fork it!
2. Create your feature branch: `git checkout -b my-new-feature`
3. Commit your changes: `git commit -am 'Add some feature'`
4. Push to the branch: `git push origin my-new-feature`
5. Submit a pull request :D


## Credits

Based on the route planning algorithm created by [Randal Olson](http://www.randalolson.com/2015/03/08/computing-the-optimal-road-trip-across-the-u-s/) and the single-script implementation of it designed by [Andrew Liesenger](https://github.com/rhiever/Data-Analysis-and-Machine-Learning-Projects/blob/master/optimal-road-trip/OptimalRoadTripHtmlSaveAndDisplay.py)

## License

All material in this repository is made available under the [Creative Commons Attribution license](https://creativecommons.org/licenses/by/4.0/). The following is a human-readable summary of (and not a substitute for) [the full legal text of the CC BY 4.0 license](https://creativecommons.org/licenses/by/4.0/legalcode).

You are free to:

Share—copy and redistribute the material in any medium or format
Adapt—remix, transform, and build upon the material
for any purpose, even commercially.

The licensor cannot revoke these freedoms as long as you follow the license terms.

Under the following terms:

Attribution—You must give appropriate credit, provide a link to the [license](https://creativecommons.org/licenses/by/4.0/), and indicate if changes were made. You may do so in any reasonable manner, but not in any way that suggests the licensor endorses you or your use.
No additional restrictions—You may not apply legal terms or technological measures that legally restrict others from doing anything the license permits.

Notices:

You do not have to comply with the license for elements of the material in the public domain or where your use is permitted by an applicable exception or limitation.
No warranties are given. The license may not give you all of the permissions necessary for your intended use. For example, other rights such as publicity, privacy, or moral rights may limit how you use the material.
###Software

Except where otherwise noted, the example programs and other software provided in this repository are made available under the [OSI](http://opensource.org/)-approved [MIT license](http://opensource.org/licenses/mit-license.html).

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
