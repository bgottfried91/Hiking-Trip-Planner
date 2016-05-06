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

def buildLocDict(itinTable):
	cursor = conn.execute("SELECT * FROM itin")
	for row in cursor:
		locDict[row[0]]=row
	return locDict
	

	
def getTemps():
	counter=0				#Needed to control number of API hits per day
	stop=0
	readC = conn.cursor()
	writeC = conn.cursor()
	itins = conn.execute("SELECT * FROM itin")
	year="2015"
	for row in itins: #Check each itinerary
		print row
		#doneSQL = "SELECT rowid FROM Weather WHERE ID=%i AND TIME=julianday('%s')" % (row[0],"2015/12/31")
		#print doneSQL
		readC.execute("SELECT rowid FROM Weather WHERE ID=%i AND TIME=julianday('%s')" % (row[0],"%s-12-31" % (year)))
		done=readC.fetchone()
		if done is not None: continue		#Skip location if already fully retrieved
		if row[5]: loc=row[5]
		else: loc=row[1]
		LATLONG=filter(lambda x: x in string.printable,loc).strip()		#Strip out non-printables
		print LATLONG
		for month in range(1,13):
			mString=str(month).zfill(2)
			readC.execute("SELECT rowid FROM Weather WHERE ID=%i AND TIME=julianday('%s')" % (row[0],"%s-%s-31" % (year,mString)))
			monthDone=readC.fetchone()
			if monthDone: continue	#Skip month if already fully retrieved
			if month==2: endDate=29
			elif ((month<=7)and(month%2==1))or((month>7)and(month%2==0)): endDate=32
			else: endDate=31
			for day in range(1,endDate):
				dString=str(day).zfill(2)
				readC.execute("SELECT rowid FROM Weather WHERE ID=%i AND TIME=julianday('%s')" % (row[0],"%s-%s-%s" % (year,mString,dString)))
				dayDone = readC.fetchone()
				print "SELECT rowid FROM Weather WHERE ID=%i AND TIME=julianday('%s')" % (row[0],"%s-%s-%s" % (year,mString,dString)), "=",dayDone
				if dayDone: continue	#Skip day if already retrieved
				DATE="%s%s%s" % (year,mString,dString)
				print DATE
				apiReq=APIbase+DATE+"/q/"+LATLONG+".json"
				print apiReq
				try:
					response=requests.get(apiReq).json()
				except ConnectionError as error:
					print error
					stop=1
					break
				time.sleep(7)			#Delay to ensure API per-minute limit isn't exceeded
				counter+=1
				if counter%10==0: print "Retrieved %i dates" % (counter)
				dbDate="%s-%s-%s" % (year,mString,dString)
				max=response["history"]["dailysummary"][0]["maxtempi"]
				min=response["history"]["dailysummary"][0]["mintempi"]
				precip=response["history"]["dailysummary"][0]["precipi"]
				sql="INSERT INTO Weather VALUES(%i,julianday('%s'),'%s','%s','%s')" % (row[0],dbDate,max,min,precip)
				print sql
				writeC.execute(sql)
				conn.commit()
				# tempDict[location,month,day,"max"]=response["history"]["dailysummary"][0]["maxtempi"]
				# tempDict[location,month,day,"min"]=response["history"]["dailysummary"][0]["mintempi"]
				# tempDict[location,month,day,"precip"]=response["history"]["dailysummary"][0]["precipi"]
				# tempDict[location,month,day]=1
				if (counter>=stopCount or stop==1): break
			if (counter>=stopCount or stop==1): break
			# tempDict[location,month]=1
		if (counter>=stopCount or stop==1): break
		# tempDict[location]=1
		
def getDates(threshold,dbManager=None,dtArray=None):
	if dbManager is None:
		conn = sqlite3.connect(db)
		closeConn=1
	else:
		conn=dbManager.conn
		closeConn=0
	counter=0				#Needed to control number of API hits per day
	stop=0
	stopCount = 500
	if dtArray is None: dtArray = []	#respect the passed in list, if one threshold wasn't enough
	readC = conn.cursor()
	writeC = conn.cursor()
	itins = conn.execute("SELECT * FROM itin")
	year="2015"
	for row in itins:
		prevDay = 0	#reset on each location
		loc = None
		if row[6]: loc=row[6]	#Get weather latlong first
		if not loc: loc=row[4]	#if no weather, try trailhead
		if not loc : loc=row[2]	#if no trailhead, use name
		LATLONG=filter(lambda x: x in string.printable,loc).strip()		#Strip out non-printables
		for month in range(1,13):
			prevDay = 0	#reset on each month
			mString=str(month).zfill(2)
			if month==2: endDate=29
			elif ((month<=7)and(month%2==1))or((month>7)and(month%2==0)): endDate=32
			else: endDate=31
			for day in range(1,endDate):
				dString=str(day).zfill(2)
				sql="SELECT * FROM Weather WHERE ID={} AND DATE='{}'".format(row[0],"{}-{}-{}".format(year,mString,dString))
				readC.execute(sql)
				dayDone = readC.fetchone()
				if dayDone is not None:
					if dayDone[2]>0: continue	#Skip day if max is >0, as it's already been retrieved
				if (day-prevDay)<threshold: continue	#Also skip if it's too close to the last day gathered
				counter = counter+1
				prevDay=day
				dtArray.append(str(row[0])+chr(9)+loc+chr(9)+"%s-%s-%s" % (year,mString,dString))
				if (counter>=stopCount or stop==1): break
			if (counter>=stopCount or stop==1): break
		if (counter>=stopCount or stop==1): break
	if closeConn==1:
		for cnt in dtArray:
			print cnt
		conn.close()
				
def getTempsSpaced():
	dbManager = DatabaseManager(db)
	dtArray=[]
	counter=0
	for threshold in reversed(range(1,5)):
		getDates(threshold,dbManager,dtArray)
		if len(dtArray)==500: break
	for date in dtArray:
		print(date)
		stop=getOneTemp(date,dbManager)
		counter+=1
		if counter%10==0: print "Retrieved %i dates" % (counter)
		if stop==1: break
		time.sleep(7)			#Delay to ensure API per-minute limit isn't exceeded
	dbManager.conn.close()

def getOneTemp(dateString,dbManager):
	if dbManager is None:
		conn = sqlite3.connect(db)
		closeConn=1
		writeC = conn.cursor
	else:
		conn = dbManager.conn
		closeConn=0
		writeC = dbManager.cur
	stop=0
	info=dateString.split(chr(9))
	loc=info[1]
	date=info[2].split("-")	#year-month-date
	apiDate="%s%s%s" % (date[0],date[1],date[2])
	apiReq=APIbase+apiDate+"/q/"+loc+".json"
	try:
		response=requests.get(apiReq).json()
	except ConnectionError as error:
		print error
		stop=1
	if stop==1: return stop
	dbDate=info[2]	#database uses year-month-date format
	try:
		max=float(response["history"]["dailysummary"][0]["maxtempi"])
		min=float(response["history"]["dailysummary"][0]["mintempi"])
		precip=float(response["history"]["dailysummary"][0]["precipi"])
	except KeyError as error:
		print error
		return 0	#If missing values, don't add to DB
	if stop==1: return stop
	sql="INSERT OR REPLACE INTO weather VALUES(%i,'%s','%s','%s','%s')" % (int(info[0]),dbDate,max,min,precip)
	print sql
	try:
		dbManager.query(sql)
	except sqlite3.IntegrityError as e:
		sql="UPDATE weather SET MAX={},MIN={},PRECIP={} WHERE ID=info[0] AND DATE=dbDate".format(max,min,int)
		print sql
		#writeC.execute(sql)
	conn.commit()
	if closeConn:conn.close()
	return stop
	
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
	dtArr=(doy-2,doy-1,doy,doy+1,doy+2)
	dataArr={2:"High",3:"Low",4:"Precip"}
	for otherDate in dtArr:
		if otherDate<1:
			continue	#If date is Jan 3rd or before, ignore earlier days
		key=(row[0],otherDate)	#Dictionary key is primary key of table
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
	noaaDB=DatabaseManager('NOAAtemps.db')
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
