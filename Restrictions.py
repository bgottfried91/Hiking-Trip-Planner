'''
Created on Apr 27, 2016

@author: Brian
'''
class Restrictions(object):
    def __init__(self,sd=None,ed=None,sl=None,el=None,rLocs=None,startDriveTime=None,endDriveTime=None):
        self.startDate=sd
        self.endDate=ed
        self.startLoc=sl
        self.endLoc=el
        self.restrictedLocations=rLocs
        if startDriveTime is not None or endDriveTime is not None:
            self.timeRestrictions=[startDriveTime,endDriveTime]