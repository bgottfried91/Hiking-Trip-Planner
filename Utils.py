'''
Created on Apr 27, 2016

@author: Brian
'''

import datetime
import googlemaps

#Stolen (with modification) from http://stackoverflow.com/questions/100210/what-is-the-standard-way-to-add-n-seconds-to-datetime-time-in-python
def addTime(dtTm, days=None,minutes=None,secs=None,restrictions=None):
    fulldate = datetime.datetime(dtTm.year, dtTm.month, dtTm.day, dtTm.hour, dtTm.minute, dtTm.second)
    if days is not None:
        fulldate = fulldate + datetime.timedelta(days=days)
    if minutes is not None:
        fulldate = fulldate + datetime.timedelta(minutes=minutes)
    if secs is not None:
        fulldate = fulldate + datetime.timedelta(seconds=secs)
    try:
        timeRes=restrictions.timeRestrictions
    except AttributeError:
        timeRes=None
    if timeRes is not None: #If we've restricted certain hours as non-driveable, respect that when adding seconds.
        time=fulldate.time()
        if timeRes[0] is not None and time<timeRes[0]: #If we're before minimum driving time, use minimum driving time as new hour and minute
            fulldate= fulldate.replace(hour=timeRes[0].hour,minute=timeRes[0].minute,second=timeRes[0].second)
        elif timeRes[1] is not None and time>timeRes[1]:   #If we're after max driving time, increment to next day and set minimum driving time for hour and minute
            try:    #Try to increment the day
                fulldate.replace(day=fulldate.day+1)
            except ValueError:  #If last day of the month, try to increment month and set day to 1
                try:
                    fulldate.replace(month=fulldate.month+1,day=1)
                except ValueError:  #If last day of the year AND last day of the month, increment year and set month and day to 1
                    fulldate.replace(year=fulldate.year+1,month=1,day=1)
            fulldate= fulldate.replace(hour=timeRes[0].hour,minute=timeRes[0].minute,second=timeRes[0].second)   #Replace hours and minutes
    return fulldate

def getGMapsVal(source,target,val,localDict):
    cachedVal=localDict.get(frozenset([source,target]))
    if cachedVal is not None: return cachedVal
    wpData=getOneWP(source,target)
    if val=="dist": return wpData[0]
    elif val=="dur": return wpData[1]
    else: return None
    
def getOneWP(db,apiKey,source,target):
    retArr=[]
    conn=db.conn
    cursor=conn.cursor()
    sql = "select * from waypoints_raw where source_mapLoc=? and target_mapLoc=?"
    ret=cursor.execute(sql,(source,target)).fetchone() 
    if ret is not None:    #Reuse if we already got it
        return ret[2:]
    print("retrieving new waypoint")
    gmaps = googlemaps.Client(apiKey)
    route = gmaps.distance_matrix(origins=[source], destinations=[target], mode="driving", # Change to "walking" for walking directions,
                                                      # # "bicycling" for biking directions, etc.
                                    language="English",
                                    units="imperial")
        
    # # "distance" is in meters
    retArr.append(route["rows"][0]["elements"][0]["distance"]["value"])

    # # "duration" is in seconds
    retArr.append(route["rows"][0]["elements"][0]["duration"]["value"])
    sql = "insert into waypoints_raw(source_mapLoc,target_mapLoc,distance,duration) values(?,?,?,?)"
    cursor.execute(sql,(source,target,retArr[0],retArr[1]))
    conn.commit()
    return retArr
        