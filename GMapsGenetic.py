"""
Randy Olson's Shortest Route Program modified By Andrew Liesinger to:
	1: Detect waypoints file at runtime - if found use it, otherwise look up distances via google calls (and then save to waypoint file)
	2: Dynamically create and open an HTML file showing the route when a shorter route is found
	3: Make it easier to tinker with the Generation / Population parameters
"""
import googlemaps
import random
import webbrowser
import datetime
import sys
import string
from lxml import etree
from __builtin__ import str, int
from DBManager import DatabaseManager
from Solution import Solution
from Utils import addTime,getOneWP
from Itinerary import Itinerary
from Restrictions import Restrictions
from numpy import less
from copy import deepcopy

GOOGLE_MAPS_API_KEY = "AIzaSyDq2t0W22vTDbViGa3o6Zq-PJq8S3vLBl4"

#This is the general filename - as shorter routes are discovered the Population fitness score will be inserted into the filename
#so that interim results are saved for comparison.  The actual filenames using the default below will be:
#Output_<Population Fitness Score>.html 
output_file = 'Output.html'

#parameters for the Genetic algorithm
thisRunGenerations=5000
thisRunPopulation_size=200
#restLocs=set([42,43,44,29,30,31,32,28,21,22,23,24,15,16,17,19,3,4,5,6,7,8,9,25,62,63,64,65,66,67])
#rest=Restrictions(datetime.datetime(2016,5,8),datetime.datetime(2016,6,22),"30577 Atlanta Lane, Westlake, OH 44145","Raleigh, NC",restLocs,datetime.time(hour=9),datetime.time(hour=20))
#restLocs=set([])


def compute_fitness_alt(solution,itinList,restrictions=None):
	solution_fitness = 0.0
	solution_dist = 0
	solution_tempOffset = 0.0
	openDays=0
	tempCount = 0
	tempOffsets=[]
	startDriveTime=0
	endDriveTime=0
	startDate=None
	endDate=None
	
	if restrictions is not None:
		startDate=restrictions.startDate
		endDate=restrictions.endDate
		startLoc=restrictions.startLoc
		endLoc=restrictions.endLoc
		if startLoc is not None:
			firstLoc=itinList[solution.solutionList[0]]		
			try:
				solution_dist+=waypoint_distances[frozenset([startLoc,firstLoc.trailhead])]
				startDriveTime=waypoint_durations[frozenset([startLoc,firstLoc.trailhead])]
			except KeyError:
				getStartEndData(1, solution, startLoc)
				solution_dist+=waypoint_distances[frozenset([startLoc,firstLoc.trailhead])]
				startDriveTime=waypoint_durations[frozenset([startLoc,firstLoc.trailhead])]
		if endLoc is not None:
			lastLoc=itinList[solution.solutionList[len(solution.solutionList)-1]]
			try:
				solution_dist+=waypoint_distances[frozenset([lastLoc.trailhead,endLoc])]
				endDriveTime=waypoint_durations[frozenset([lastLoc.trailhead,endLoc])]
			except KeyError:
				getStartEndData(2, solution, endLoc)
				solution_dist+=waypoint_distances[frozenset([lastLoc.trailhead,endLoc])]
				endDriveTime=waypoint_durations[frozenset([lastLoc.trailhead,endLoc])]
	
	if startDate is None:
		date=datetime.datetime.today()
	else:
		date=startDate
	if startDriveTime is not None:
		date=addTime(startDate, secs=startDriveTime,restrictions=restrictions)	#Add drive time to first location to start date
	for index in range(len(solution.solutionList)):
		if index>0:
			startWaypoint = solution.solutionList[index-1]
			destWaypoint = solution.solutionList[index]
			destItin=itinList[destWaypoint]	#Get the itinerary object for the destination, so that the temperature can be retrieved from it
		else:
			destItin=itinList[solution.solutionList[index]]	#If first location, set destination appropriately
		#Get temperature data
		temps=[]
		tempHigh=None
		tempLow=None
		idealTemp=80-(3.5*(destItin.weatherLocElevation/1000))
		temps=destItin.getTemp(date)	#[maxTemp,minTemp] format
		try:
			tempHigh=temps[0]
			tempLow=temps[1]
			if tempHigh is not None and ((tempHigh<(idealTemp-10)) or (tempHigh>(idealTemp+10))):
				tempCount+=1
				tempOffsets.append(abs(idealTemp-tempHigh))
		except TypeError:
			doy=int(date.strftime('%j'))
			print("No temperature data for {}-{} on day {}".format(destItin.id,destItin.parkName,doy))
				#Get distance data
		date = addTime(date, days=destItin.los, restrictions=restrictions)
		if endDate is not None and date>endDate: return float("inf")	#If the itinerary passes end date, it's invalid
		if index>0:
			try:
				solution_dist += waypoint_distances[frozenset([startWaypoint,destWaypoint])]
			except:
				print("Unable to retrieve distance data for %s to %s" % (startWaypoint,destWaypoint))
			date = addTime(date,secs=waypoint_durations[frozenset([startWaypoint,destWaypoint])],restrictions=restrictions)	#Add travel time to most recent date
			if endDate is not None and date>endDate: return float("inf")	#If the itinerary passes end date, it's invalid
	#Check return date
	if endDate is not None:
		date = addTime(date, secs=endDriveTime,restrictions=restrictions)
		if date>endDate: return float("inf")
		openDays=(endDate-date).days
	else:
		openDays=0	
	solution_fitness +=solution_dist	#firstly, add distance
	for index in range(0,tempCount):
		solution_tempOffset += tempOffsets[index]
	solution_fitness += (9654 * solution_tempOffset)		#and now add in the temp offsets
	solution_fitness=(solution_fitness/len(solution.solutionList))	#Now adjust by # of locations in list, to ensure we compare solutions evenly even with different #s of dests
	if openDays>3: solution_fitness+=(9654*(openDays**2))
	solution.endDate=date	#Record end date calculated here, to avoid recalculating it if not necessary
	return solution_fitness
		
def compute_fitness(solution):
	"""
		This function returns the total distance traveled on the current road trip.
		
		The genetic algorithm will favor road trips that have shorter
		total distances traveled.
	"""
	
	solution_fitness = 0.0
	
	for index in range(len(solution)):
		waypoint1 = solution[index - 1]
		waypoint2 = solution[index]
		#try:
		solution_fitness += waypoint_distances[frozenset([waypoint1, waypoint2])]
		#except Exception as e:	#if cannot compute distance for some reason, disregard this solution
			#solution_fitness = 9999999999999.00
			#break
		
	return solution_fitness


def mutate_agent(sourceGenome, max_mutations=3,restrictions=None):
	"""
		Creates an n-point mutation of the sourceGenome
		
		A point mutation swaps the order of two waypoints in the road trip.
	"""
	
	agent_genome = deepcopy(sourceGenome)	#Create new copy of object

	num_mutations = random.randint(1, max_mutations)
	
	for mutation in range(num_mutations):
		swap_index1 = random.randint(0, len(agent_genome.solutionList) - 1)
		swap_index2 = swap_index1

		while swap_index1 == swap_index2:
			swap_index2 = random.randint(0, len(agent_genome.solutionList) - 1)

		agent_genome.solutionList[swap_index1], agent_genome.solutionList[swap_index2] = agent_genome.solutionList[swap_index2], agent_genome.solutionList[swap_index1]
			
	return agent_genome

def shuffle_mutation(sourceGenome,restrictions=None):
	"""
		Creates shuffle mutation of sourceGenome.
		
		A shuffle mutation takes a random sub-section of the road trip
		and moves it to another location in the road trip.
	"""
	
	agent_genome = deepcopy(sourceGenome)	#Create new copy of object
	
	start_index = random.randint(0, len(agent_genome.solutionList) - 1)
	length = random.randint(2, 20)
	
	genome_subset = agent_genome.solutionList[start_index:start_index + length]
	agent_genome.solutionList = agent_genome.solutionList[:start_index] + agent_genome.solutionList[start_index + length:]
	
	insert_index = random.randint(0, len(agent_genome.solutionList) + len(genome_subset) - 1)
	agent_genome.solutionList = agent_genome.solutionList[:insert_index] + genome_subset + agent_genome.solutionList[insert_index:]
	
	return agent_genome

def generate_random_population(pop_size,restrictions=None):
	"""
		Generates a list with `pop_size` number of random road trips.
	"""
	
	random_population = []
	for agent in range(pop_size):
		newAgent=generate_random_agent(restrictions)
		random_population.append(newAgent)
	return random_population

def generate_random_agent(restrictions=None):
	"""
		Creates a random road trip from the waypoints.
	"""
	new_random_agent = Solution(all_waypoints[:],restrictions)
	random.shuffle(new_random_agent.solutionList)
	applyRestrictions(new_random_agent,restrictions)
	return new_random_agent
	
	
def run_genetic_algorithm(generations=5000, population_size=100,itinList=[],restrictions=None):
	"""
		The core of the Genetic Algorithm.
	"""
	current_best_distance =-1
	best_fitness=float("inf")
	
	# Create a random population of `population_size` number of solutions.
	population = generate_random_population(population_size,restrictions)
	topPopcutoff=population_size/10		#Get # of solutions to keep based on 10% of size

	# For `generations` number of repetitions...
	for generation in range(generations):
		
		# Compute the fitness of the entire current population
		population_fitness = {}

		for agent_genome in population:
			if agent_genome in population_fitness:	#Don't reevaluate if we checked an identical solution earlier in this generation
				agent_genome.fitness=population_fitness[agent_genome]
				continue
			# if hasattr(agent_genome, "fitness"):	#If solution has fitness from a previous generation, also don't recheck
				#--------- population_fitness[agent_genome]=agent_genome.fitness
				#------------------------------------------------------ continue
			try:
				old_fitness=getattr(agent_genome, "fitness")
			except AttributeError:
				old_fitness=None
			agent_fitness = compute_fitness_alt(agent_genome,itinList,restrictions)
# 			if (old_fitness is not None) and agent_fitness!=old_fitness:
# 				print("This solution's fitness changed from {} to {}:".format(old_fitness,agent_fitness))
# 				print(agent_genome.solutionList)
			population_fitness[agent_genome] = agent_fitness
			agent_genome.fitness=agent_fitness	#Store fitness in object
			if agent_genome.fitness<best_fitness: 
				best_fitness=agent_genome.fitness
				best_gen=generation
				best_sol=deepcopy(agent_genome)
			#population_fitness[agent_genome] = compute_fitness(agent_genome)

		# Take the 10 shortest road trips and produce 10 offspring each from them
		new_population = []
		topPop=[]
		topPop=sorted(population_fitness, key=population_fitness.get)[:topPopcutoff*2]
		for rank, agent_genome in enumerate(topPop):
			if (generation % 1000 == 0 or generation == generations - 1) and rank == 0:
				current_best_genome = agent_genome
				print("Generation {} best: {} | Unique genomes: {}".format(generation,population_fitness[agent_genome],len(population_fitness)))
				print(agent_genome.solutionList)				
				print("")

				#if this is the first route found, or it is shorter than the best route we know, create a html output and display it
				if (agent_genome.fitness < current_best_distance) or (current_best_distance < 0):
					current_best_distance = population_fitness[agent_genome]
					#CreateOptimalRouteHtmlFile(agent_genome,current_best_distance, 0)
					

			# Create 1 exact copy of each of the top road trips
			#===================================================================
			# if rank==0 and agent_genome.fitness>best_fitness:
			# 	print("In generation {}, the top ranked fitness was {}, but we recorded a better fitness of {} in generation {}".format(generation,agent_genome.fitness,best_fitness,best_gen))
			#===================================================================
			new_population.append(deepcopy(agent_genome))
			
			pointMuts=min(int(topPopcutoff*.2/2),len(agent_genome.solutionList)-1)
			# Create offspring with 1-3 point mutations
			for offspring in range(pointMuts):
				new_population.append(mutate_agent(agent_genome,3,restrictions))
				
			shuffleMuts=min(int(topPopcutoff*.5/2),len(agent_genome.solutionList)-1)
			# Create offspring with a single shuffle mutation
			for offspring in range(shuffleMuts):
				new_population.append(shuffle_mutation(agent_genome,restrictions))
			
			#Add in some random offspring to help encourage diversity
			randomMuts=min(int(topPopcutoff*.2/2),len(agent_genome.solutionList)-1)
			for offspring in range(randomMuts):
				new_population.append(generate_random_agent(restrictions))

		# Replace the old population with the new population of offspring 
		oldTop=deepcopy(topPop)	#Save off for debugging purposes
		oldPopFitness=population_fitness.copy()
		del population[:]

		population = new_population
		

		
	print("The best fitness overall was {}".format(best_fitness))
	print("The best distance overall was {}".format(current_best_distance))
	return current_best_genome


#Various utility functions
def applyRestrictions(solution,restrictions):
	if restrictions.startLoc is not None:
		getStartEndData(1, solution, restrictions.startLoc)
	if restrictions.endDate is not None:
		try:
			startDate=restrictions.startDate
		except AttributeError:
			startDate=datetime.datetime.today()	#If no start date specified, assume today
		date=startDate
		if restrictions.startLoc is not None:
			date=addTime(date, secs=waypoint_durations[frozenset([restrictions.startLoc,getItinFromItinList(solution.solutionList[0]).trailhead])],restrictions=restrictions)	#Add in driving time to first location
		prevItin=None
		listLength=0
		oldSolution=solution.solutionList[:]
		for itin in solution.solutionList:
			date = date + datetime.timedelta(days=itinList[itin].los) #Add LOS from current location to the date to be used for temp measurement
			startPlusLOS=deepcopy(date)
			if prevItin is not None: date = addTime(date,secs=waypoint_durations[frozenset([prevItin,itin])],restrictions=restrictions)	#Add travel time to most recent date
			startPlusLOSPlusTravel= deepcopy(date)
			if (date-restrictions.endDate).days<0: 
				listLength+=1
			else: break	#Don't bother continuing if we hit an end point
			prevItin=itin
		listTruncate=max(listLength-1,1)	#Need a minimum of 1, because if you truncate to the 0th element, it's an empty list
		if len(solution.solutionList)>1: solution.solutionList=solution.solutionList[:listTruncate]	#Truncate list to the number of itins before the end date, but don't make it an empty list
		if len(solution.solutionList)==0: print("List was truncated to nothing") 
	if restrictions.endLoc is not None:
		getStartEndData(2, solution, restrictions.endLoc)
	return solution

def getItinList(db,restrictions=None):
	outputList={}
	itins = db.query("select * from itin")
	for itin in itins:
		if restrictions is not None and getattr(restrictions,"restrictedLocations") is not None and itin[0] in restrictions.restrictedLocations: continue	#Ignore any restricted locations when building list
		itinId=itin[0]
		weatherLoc=itin[6]
		weatherLocElevation=db.conn.cursor().execute("select elevation from stations where noaaID=?",(weatherLoc,)).fetchone()[0]
		outputList[itinId]=Itinerary(db,itinId,itin[1],itin[2],itin[3],itin[4],itin[5],weatherLoc,itin[7],itin[8],itin[9],itin[10],itin[11],itin[12],itin[13],itin[14],weatherLocElevation)
	return outputList

			
def getStartEndData(startOrEnd=None,solution=None,otherLoc=None):
	if startOrEnd==1:
		firstLoc=getItinFromItinList(solution.solutionList[0])
		mapsVals=getOneWP(dbManager,GOOGLE_MAPS_API_KEY,otherLoc, firstLoc.trailhead)
		waypoint_distances[frozenset([otherLoc,firstLoc.trailhead])]=mapsVals[0]
		waypoint_durations[frozenset([otherLoc,firstLoc.trailhead])]=mapsVals[1]
	else:
		lastLoc=getItinFromItinList(solution.solutionList[len(solution.solutionList)-1])
		mapsVals=getOneWP(dbManager,GOOGLE_MAPS_API_KEY,lastLoc.trailhead,otherLoc)
		waypoint_distances[frozenset([lastLoc.trailhead,otherLoc])]=mapsVals[0]
		waypoint_durations[frozenset([lastLoc.trailhead,otherLoc])]=mapsVals[1]

def getItinFromItinList(itinId):
	global itinList
	return itinList[itinId]

def checkRandoms(pop):
	randDict={}
	dupCount=0
	for sol in pop:
		if sol in randDict:
			dupCount+=1
		else:
			randDict[sol]=1
	print("Found {} duplicates in random solution".format(dupCount))

def getRestrictions():
	startDate=getDateFromString(sys.argv[1])
	endDate=getDateFromString(sys.argv[2])
	startLoc=sys.argv[3]
	endLoc=sys.argv[4]
	restLocs=set()
	for loc in sys.argv[5].split(","):
		restLocs.add(int(loc.strip(string.punctuation)))
	morningTime=getTimeFromString(sys.argv[6])
	eveningTime=getTimeFromString(sys.argv[7])
	return Restrictions(sd=startDate,ed=endDate,sl=startLoc,el=endLoc,rLocs=restLocs,startDriveTime=morningTime,endDriveTime=eveningTime)
	
def getDateFromString(string):
	return datetime.datetime.strptime(string,"%x")

def getTimeFromString(string):
	return (datetime.datetime.strptime(string,"%X").time())

def testFitness():
	restLocs=set([42,43,44,29,30,31,32,28,21,22,23,24,15,16,17,19,3,4,5,6,7,8,9,25,62,63,64,65,66,67])
	rest=Restrictions(datetime.datetime(2016,5,8),datetime.datetime(2016,6,22),"30577 Atlanta Lane, Westlake, OH 44145","Raleigh, NC",restLocs,datetime.time(hour=9),datetime.time(hour=20))
	db=DatabaseManager("hikingData.db")
	itinList=getItinList(db, rest)
	solution=Solution([41, 96, 98, 46, 13, 68, 69, 88, 33, 53, 49, 57, 80, 85, 86],rest)
	waypoint_distances={}
	waypoint_durations={}
	for row in db.query("select * from waypoints"):	#populate distances and durations arrays from SQL database
			waypoint_distances[frozenset([row[0],row[1]])] = row[4]
			waypoint_durations[frozenset([row[0],row[1]])] = row[5]
	prevFitness=None
	for index in range(1,100):
		fitness=compute_fitness_alt(solution, itinList, rest)
		if prevFitness is not None and fitness!=prevFitness:
			print("This solution's fitness changed from {} to {}:".format(prevFitness,fitness))
		prevFitness=fitness
		
#Output functions		
def createXML(db,solution,itinList,restrictions):
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
		date=addTime(date,secs=waypoint_durations[frozenset([startLoc,getItinFromItinList(solution.solutionList[0]).trailhead])],restrictions=restrictions)
		etree.SubElement(startNode,"distance").text=str(waypoint_distances[frozenset([startLoc,getItinFromItinList(solution.solutionList[0]).trailhead])])
	for location in solution.solutionList:
		itin=getItinFromItinList(location)
		itinNode=etree.SubElement(root,"location")
		if prevLocation is not None:
				date = addTime(date,secs=waypoint_durations[frozenset([prevLocation,location])],restrictions=restrictions)	#Add travel time to most recent date if not first location
		if prevNode is not None:
			distNode=etree.SubElement(prevNode,"distance")
			distNode.text=str(waypoint_distances[frozenset([prevLocation,location])])
		arrivalNode=etree.SubElement(itinNode,"arrivalDate")
		arrivalNode.text=str(date.isoformat())
		#Get all static data in itin item
		for att in itin.__dict__.keys():
			if not (att=="tempArr" or att=="conn" or att=="db"): 	#skip any non-base types for now
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
		etree.SubElement(prevNode,"distance").text=str(waypoint_distances[frozenset([getItinFromItinList(prevLocation).trailhead,endLoc])])
		endNode=etree.SubElement(root,"end_location")
		endNode.text=str(endLoc)
		endDate=addTime(date, secs=waypoint_durations[frozenset([getItinFromItinList(prevLocation).trailhead,endLoc])],restrictions=restrictions)
		etree.SubElement(endNode,"arrivalDate").text=str(endDate.isoformat())
	#print(etree.tostringlist(root, pretty_print=True))
	open("secondLeg/route"+fitness+".xml","wb").write(etree.tostring(root, pretty_print=True))
	xslt=etree.XSLT(etree.parse("xslTrans.xsl"))
	html=xslt(root)
	html.write("route.html")
	webbrowser.open_new_tab("route.html")
	

if __name__ == '__main__':
	# if this file exists, read the data stored in it - if not then collect data by asking google
	print("Begin finding shortest route")
	rest=getRestrictions()
	all_waypoints = []
	dbManager = DatabaseManager("hikingData.db")
	#Global settings; change these to modify how the program calculates the route
	#rest=None
	conn = dbManager.conn
	cursor = conn.cursor()
	itins = cursor.execute("select * from itin")
	itinList=getItinList(dbManager)
	waypoint_distances={}
	waypoint_durations={}
	for itin in itinList:
		all_waypoints.append(itin)
	for row in dbManager.query("select * from waypoints"):	#populate distances and durations arrays from SQL database
			waypoint_distances[frozenset([row[0],row[1]])] = row[4]
			waypoint_durations[frozenset([row[0],row[1]])] = row[5]
	print("Search for optimal route")
	optimal_route = run_genetic_algorithm(generations=thisRunGenerations, population_size=thisRunPopulation_size,itinList=itinList,restrictions=rest)
	createXML(dbManager, optimal_route, itinList,rest)
	#CreateOptimalRouteHtmlFile(optimal_route, 0)
	

