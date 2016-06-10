'''
Created on Apr 27, 2016

@author: Brian
'''

import random
import datetime
from lxml import etree
from Utils import addTime, getGMapsVal
import webbrowser

class Solution(object):
    def __init__(self,waypoints,restrictions=None):
        if restrictions is not None and restrictions.restrictedLocations is not None:
            self.solutionList=[itin for itin in waypoints if itin not in restrictions.restrictedLocations]  #Don't include restricted locations in the solution list
        else:
            self.solutionList=waypoints
        if self.solutionList==[]: return None
        self.solutionSet=set(waypoints)
    
    def shuffle(self):
        random.shuffle(self.solutionList)
        
    def updateSet(self):
        self.solutionSet=set(self.solutionList)

    def __hash__(self):
        return hash(tuple(self.solutionList))

    def __eq__(self, other):
        return (self.solutionList) == (other.solutionList)

    def __ne__(self, other):
        # Not strictly necessary, but to avoid having both x==y and x!=y
        # True at the same time
        return not(self.solutionList == other.solutionList)
    
    def createXML(self,db,solution,itinList,restrictions,waypoint_distances={},waypoint_durations={}):
        try:
            startDate=restrictions.startDate
        except AttributeError:
            startDate=datetime.datetime.today()
        try:
            endDate=restrictions.endDate
        except AttributeError:
            endDate=None
        try:
            startLoc=restrictions.startLoc
        except AttributeError:
            startLoc=None
        try:
            endLoc=restrictions.endLoc
        except AttributeError:
            endLoc=None
        date=startDate
        root=etree.Element("solution")
        etree.SubElement(root,"itinList").text=str(solution.solutionList)
        fitness=str(solution.fitness)
        fitnessNode=etree.SubElement(root,"fitness")
        fitnessNode.text=fitness
        try:
            etree.SubElement(root,"end_date").text=str(solution.endDate.isoformat())
        except AttributeError:
            etree.SubElement(root,"end_date").text="No end date recorded"
        prevLocation=None
        prevNode=None
        if startLoc is not None:
            startNode=etree.SubElement(root,"start_location")
            startNode.text=startLoc
            etree.SubElement(startNode,"departureDate").text=startDate.isoformat()
            date=addTime(date,secs=getGMapsVal(startLoc,itinList[solution.solutionList[0]].trailhead,"dur",waypoint_durations),restrictions=restrictions)
            etree.SubElement(startNode,"distance").text=str(getGMapsVal(startLoc,itinList[solution.solutionList[0]].trailhead,"dist",waypoint_distances))
        for location in solution.solutionList:
            itin=itinList[location]
            itinNode=etree.SubElement(root,"location")
            if prevLocation is not None:
                    date = addTime(date,secs=getGMapsVal(prevLocation,location,"dur",waypoint_durations),restrictions=restrictions)    #Add travel time to most recent date if not first location
            if prevNode is not None:
                distNode=etree.SubElement(prevNode,"distance")
                distNode.text=str(getGMapsVal(prevLocation,location,"dist",waypoint_distances))
            arrivalNode=etree.SubElement(itinNode,"arrivalDate")
            arrivalNode.text=str(date.isoformat())
            #Get all static data in itin item
            for att in itin.__dict__.keys():
                if not (att=="tempArr" or att=="conn" or att=="db"):     #skip any non-base types for now
                    attNode=etree.SubElement(itinNode,att)
                    attNode.text=str(getattr(itin,att))
            #Get weather data
            try:
                expWeather=itin.tempArr[int(date.strftime("%j"))]
            except KeyError:
                expWeather="No weather data for "+str(date.isoformat())
            weatherNode=etree.SubElement(itinNode,"expectedWeather")
            weatherNode.text=str(expWeather)
            #Get departure date data
            date=date + datetime.timedelta(days=itinList[location].los)
            etree.SubElement(itinNode,"departureDate").text=str(date.isoformat())
            #Track data for loc+1
            prevLocation=location
            prevNode=itinNode
        if endLoc is not None:
            etree.SubElement(prevNode,"distance").text=str(getGMapsVal(itinList[prevLocation].trailhead,endLoc,"dist",waypoint_durations))
            endNode=etree.SubElement(root,"end_location")
            endNode.text=str(endLoc)
            endDate=addTime(date, secs=getGMapsVal(itinList[prevLocation].trailhead,endLoc,"dur",waypoint_durations),restrictions=restrictions)
            etree.SubElement(endNode,"arrivalDate").text=str(endDate.isoformat())
        #print(etree.tostringlist(root, pretty_print=True))
        open("secondLeg/route"+fitness+".xml","wb").write(etree.tostring(root, pretty_print=True))
        xslt=etree.XSLT(etree.parse("xslTrans.xsl"))
        html=xslt(root)
        html.write("route.html")
        webbrowser.open_new_tab("route.html")

