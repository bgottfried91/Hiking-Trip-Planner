import os.path
import urllib
import json
import pandas
import pickle
import string
import requests
import time
import pdb
import sqlite3
import datetime
from GMapsGenetic import Itinerary,getItinList,DatabaseManager

outputFile = "TemperatureData.csv"
apiCalls = 0
db = "hikingData.db"
itinTable = "itin"
inputFile = "Definitive Ranking of US Hiking Opportunities.csv"
locDict = {}
APIkey="2a6be0ce474d8519"
APIbase="http://api.wunderground.com/api/%s/history_" % (APIkey) #Should be concatenated with DATE/q/LATLONG.json
stopCount=500
	
def castData(castFunc,data):	#Sick of having casting fail on me
	try:
		return castFunc(data)
	except ValueError:
		if castFunc==("int" or "float"): return 0
		else: return None

def getAverages(dbManager=None):
	if dbManager is None:
		conn = sqlite3.connect(db)
		closeConn=1
	else:
		conn=dbManager.conn
		closeConn=0
	readC = conn.cursor()
	writeC = conn.cursor()
	temps=conn.execute("Select * from weather ORDER BY ID,DATE")
	avgDict=dict()
	checkCount=0
	for row in temps:
		checkCount+=1
		dates=getSurroundingDates(row,avgDict)
		if checkCount%100==0: print("Checked {} rows in weather table".format(checkCount))
	for key in sorted(avgDict.keys()):
		sum=0
		sumCnt=0
		avg={}
		for column in range(2,5):
			if column in avgDict[key].keys():
				for num in avgDict[key][column]:
					try:
						sum+=int(num)
						sumCnt+=1
					except:
						sum+=0
				if sumCnt>0:
					avg[column]=sum/sumCnt
				else:
					avg[column]=0
				avgDict[key][column]=avg[column]
			else:
				avgDict[key][column]=0
		#print "{} average: {}".format(key,avg)
		date=key[1]
		#print "Averages at {} on {}: {}={},{}={},{}={}".format(key[0],date,"High",avgDict[key][2],"Low",avgDict[key][3],"Precip",avgDict[key][4],)
		sql = "Insert Into weather_avg(ID, DOY, MAX_AVG, MIN_AVG, PRECIP_AVG) values({},{},{},{},{});".format(key[0],date,avgDict[key][2],avgDict[key][3],avgDict[key][4])
		try:
			writeC.execute(sql)
			#print sql
		except:
			"exception"
			#print("Already wrote to the line with ID={} and date={}".format(key[0],date))
	conn.commit()
	if closeConn:conn.close()

def getSurroundingDates(row,avgDict):
	date=str(row[1])
	year=int(date[:4])
	month=int(date[4:6])
	day=int(date[6:])
	dateObj=datetime.date(year,month,day)
	doy=int(dateObj.strftime("%j"))
	doyArr=(doy-2,doy-1,doy,doy+1,doy+2)
	dataArr={2:"High",3:"Low",4:"Precip"}
	for otherDOY in doyArr:
		if otherDOY<1:
			continue	#If date is Jan 3rd or before, ignore earlier days
		key=(row[0],otherDOY)	#Dictionary key is primary key of table
		if not key in avgDict:
			avgDict[key]={}		#Create inner dictionary if it doesn't already exist
		for data in dataArr.keys():
			if data in avgDict[key]:
				avgDict[key][data].append(row[data])
			else:
				avgDict[key][data]=[row[data]]
				
def getDatesFromDB(hikingDB=None):
	if hikingDB is None:
		hikingDB=DatabaseManager("hikingData.db")
	itinList=getItinList(hikingDB)
	noaaDB=DatabaseManager('NOAAData.db')
	for id in itinList:
		itin=itinList[id]
		print("Processing itin {}-{}".format(itin.id,itin.trailName))
		tempData=noaaDB.execSQL("select * from temps where noaaID=?",(itin.weatherLoc,))
		for row in tempData:
			sql="INSERT OR REPLACE INTO weather(id,date,MAX,MIN,PRECIP) VALUES(?,?,?,?,?)"
			sqlParams=(itin.id,row[1],row[2],row[3],row[4])
			hikingDB.execSQL(sql,sqlParams)
	hikingDB.conn.commit()	
	
	
				
			
if __name__ == "__main__":	
	getDatesFromDB()
	getAverages()
