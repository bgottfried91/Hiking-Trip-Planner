from itertools import combinations
import googlemaps
import pandas as pd
import numpy as np
import os.path
import random
import webbrowser
import sqlite3
from Itinerary import Itinerary

GOOGLE_MAPS_API_KEY = "AIzaSyDq2t0W22vTDbViGa3o6Zq-PJq8S3vLBl4"



class DatabaseManager(object):
	def __init__(self, db):
		self.conn = sqlite3.connect(db)
		self.conn.execute('pragma foreign_keys = on')
		self.conn.commit()
		self.cur = self.conn.cursor()

	def query(self, arg):
		self.cur.execute(arg)
		self.conn.commit()
		return self.cur

	def __del__(self):
		self.conn.close()



if __name__ == '__main__':
	itinList = []
	dbManager = DatabaseManager("hikingData.db")
	conn = dbManager.conn
	cursor = conn.cursor()
	itins = cursor.execute("select * from itin")
	for itin in itins:
		itinList.append(Itinerary(dbManager,itin[0],itin[1],itin[2],itin[3],itin[4],itin[5],itin[6],itin[7],itin[8],itin[9],itin[10],itin[11],itin[12],itin[13],itin[14]))	#append itin objects
	waypoint_distances = {}
	waypoint_durations = {}
	checkCount=0
	addCount=0
	
	#print(waypoint_distances)
	gmaps = googlemaps.Client(GOOGLE_MAPS_API_KEY)
	for (source, target) in combinations(itinList, 2):
		checkCount+=1
		#if checkCount%1000: print("Checked {} pairs".format(checkCount))
		sql = "select * from waypoints where source_ID={} and target_ID={}".format(source.id,target.id)	#Check for unique row in SQL table
		if cursor.execute(sql).fetchone() is not None:	#skip it if we already got it
			continue
		try:
			route = gmaps.distance_matrix(origins=[source.trailhead],
										destinations=[target.trailhead],
										mode="driving", # Change to "walking" for walking directions,
														  # # "bicycling" for biking directions, etc.
										language="English",
										units="metric")
	
			# # "distance" is in meters
			distance = route["rows"][0]["elements"][0]["distance"]["value"]
	
			# # "duration" is in seconds
			duration = route["rows"][0]["elements"][0]["duration"]["value"]
			sql = "insert or replace into waypoints(source_ID,target_ID,source_mapLoc,target_mapLoc,distance,duration) values ({},{},'{}','{}',{},{})".format(source.id,target.id,source.trailhead,target.trailhead,distance,duration)
			dbManager.query(sql)
			addCount+=1
			
			print("retrieved data for the route between {}-{} and {}-{}.".format(source.parkName,source.trailName,target.parkName,target.trailName))
	
		except Exception as e:
			print e
			print("Error with finding the route between %s and %s." % (source.parkName,target.parkName))
	if addCount==0: print("There were no missing pairs in the database")
