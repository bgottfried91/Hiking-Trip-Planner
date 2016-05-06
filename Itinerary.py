'''
Created on Apr 27, 2016

@author: Brian
'''

from DBManager import DatabaseManager

class Itinerary(object):
    def __init__(self, db=None, itinID=None, state=None, parkName=None, los=None, trailhead=None, trailName=None, 
                 weatherLoc=None, link=None, loop=None, busySeason=None, offTrail=None, camping=None, permit=None, permitCost=None, remarks=None,weatherLocElevation=None):
        if db is None:
            self.db=DatabaseManager("hikingData.db")
            self.conn=db.conn
        else:
            self.db=db
            self.conn=db.conn
        self.id=itinID
        self.state=state
        self.parkName=parkName
        self.los=los
        self.trailhead=trailhead
        self.trailName=trailName
        self.weatherLoc=weatherLoc
        self.link=link
        self.loop=loop
        self.busySeason=busySeason
        self.offTrail=offTrail
        self.camping=camping
        self.permit=permit
        self.permitCost=permitCost
        self.remarks=remarks
        self.weatherLocElevation=weatherLocElevation
        self.tempArr=self.getAllTemps()
        
    @classmethod
    def fromSQLRow(cls,db,sqlRow):
        return cls(db,sqlRow[0],sqlRow[1],sqlRow[2],sqlRow[3],sqlRow[4],sqlRow[5],sqlRow[6],sqlRow[7],sqlRow[8],sqlRow[9],sqlRow[10],sqlRow[11],sqlRow[12],sqlRow[13],sqlRow[14],None)
    
    @classmethod
    def getItinFromID(cls,db,id):
        sqlRow=db.execSQL("select * from itin where id=?",(id,))
        return cls(db,id,sqlRow[1],sqlRow[2],sqlRow[3],sqlRow[4],sqlRow[5],sqlRow[6],sqlRow[7],sqlRow[8],sqlRow[9],sqlRow[10],sqlRow[11],sqlRow[12],sqlRow[13],sqlRow[14],None)
        
    def getAllTemps(self):
        tempArr={}
        sql = "select * from weather_avg where id = ?"
        sqlParam = (self.id,)
        newCur = self.db.conn.cursor()    #Need a new cursor, otherwise we'll break the existing cursor that we're iterating over to create each itin
        rows = newCur.execute(sql, sqlParam)
        for row in rows:
            tempArr[row[1]]=row[2:4]
        return tempArr
            
    def getTemp(self,date):
        global temp_retrievals
        dayNum=int(date.strftime("%j"))
        try:
            temp=self.tempArr[dayNum]
        except KeyError:    #If date's not in the array already, retrieve it
            tempQuery=self.conn.cursor().execute("select MAX_AVG,MIN_AVG from weather_avg where ID = %d and DOY = %d" % (self.id,dayNum))
            temp=tempQuery.fetchone()    
            self.tempArr[dayNum]=temp    #Cache for reusing later
            temp_retrievals += 1    #tracking how many DB hits we use
            if temp_retrievals%1000==0: 
                print("Made {} DB hits so far".format(temp_retrievals))
        return temp
    
        