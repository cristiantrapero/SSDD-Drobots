#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import socket
import math
import Ice
Ice.loadSlice('factory.ice --all -I .')
import drobots
Ice.loadSlice('container.ice --all -I .')
import Services


class Functions(Ice.Application):

	# To calculate our own IP
	def getIP(self, current = None):
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		s.connect(("atclab.esi.uclm.es", 80))
		ip = s.getsockname()[0]
		s.close()
		return ip

	#To get the container where the factories are stored
	def getContainer(self, containerPort, current = None):
		broker = self.communicator()
		my_IP = self.getIP()
		proxyFactoriesContainer = broker.stringToProxy("container1 -t -e 1.1:tcp -h {} -p 909{} -t 60000".format(my_IP, containerPort))
		factoriesContainer = Services.ContainerPrx.checkedCast(proxyFactoriesContainer)
		return factoriesContainer

class Strategy(Ice.Application):

	# We want to move the defender robot to the nearest corner so we calculate where to move
	def moveRobotToCorner(self, position, current = None):
		distanceToLD = self.distanceToPoint(position, 0, 0)
		distanceToRD = self.distanceToPoint(position, 399, 0)
		distanceToLT = self.distanceToPoint(position, 0, 399)
		distanceToRT = self.distanceToPoint(position, 399, 399)

		minDistance = min(distanceToLD, distanceToLT, distanceToRD, distanceToRT)

		if(minDistance == distanceToLD):
			corner = (0, 0)
		elif (minDistance == distanceToLT):
			corner = (0, 399)
		elif (minDistance == distanceToRD):
			corner = (399, 0)
		else:
			corner = (399, 399)

		return corner

	# We want to move the complete robots to the middle point of each battlefield side, starting by the nearest
	def getNearestPoint(self, position, current = None):
		# We want to move the robot to the nearest corner
		distanceToDown = self.distanceToPoint(position, 200, 0)
		distanceToRight = self.distanceToPoint(position, 399, 200)
		distanceToUp = self.distanceToPoint(position, 200, 399)
		distanceToLeft = self.distanceToPoint(position, 0, 200)

		minDistance = min(distanceToDown, distanceToRight, distanceToUp, distanceToLeft)

		if(minDistance == distanceToDown):
			point = (200, 0)
		elif (minDistance == distanceToRight):
			point = (399, 200)
		elif (minDistance == distanceToUp):
			point = (200, 399)
		else:
			point = (0, 200)

		return point


	def distanceToPoint(self, position, coordenateX, coordenateY, current = None):
		relativeDistanceX = coordenateX - position.x
		relativeDistanceY = coordenateY - position.y
		distanceDestination = math.hypot(relativeDistanceX, relativeDistanceY)

		return distanceDestination

	def angleToPoint(self, position, coordenateX, coordenateY, current = None):
		relativeDistanceX = coordenateX - position.x
		relativeDistanceY = coordenateY - position.y
		angle = (int(math.degrees(math.atan2(relativeDistanceY, relativeDistanceX)) % 360.0))

		return angle

class RobotControllerDefender(drobots.RobotControllerDefender):
	def __init__(self, bot, id):
		self.robot = bot
		self.id = id
		self.enemies = 0
		self.robotsContainer = Functions().getContainer(1)
		self.companions = {}
		self.detectors = {}
		self.arrivalToCorner = False
		self.selectedCorner = False
		self.corner = (0,0)
		self.rangeToScan = (0,0)
		self.angleToScan = 0

		print("I'm the defender robot {}. \n".format(self.id))

	def turn(self, current = None):
		print("Defender robot{} turn. \n".format(self.id))

		# Get the robot's data
		pos = self.robot.location()
		energy = self.robot.energy()
		damage = self.robot.damage()


		if not self.arrivalToCorner:
			if not self.selectedCorner:
				# We move the robot to the nearest corner
				self.corner = Strategy().moveRobotToCorner(pos)
				self.selectedCorner = True

				#We set the range to scan, because otherwise it would scan out of the battlefield
				if(self.corner[0] == 0 and self.corner[1] == 0):
					self.rangeToScan = (0, 90)
				elif(self.corner[0] == 399 and self.corner[1] == 0):
					self.rangeToScan = (90, 180)
				elif(self.corner[0] == 0 and self.corner[1] == 399):
					self.rangeToScan = (180, 270)
				else:
					self.rangeToScan = (270, 359)

				self.angleToScan = self.rangeToScan[0]

			print ("I'm moving to corner {}.".format(self.corner))
			print("From the current position {} {}.".format(pos.x, pos.y))

			distanceDestination = Strategy().distanceToPoint(pos, self.corner[0], self.corner[1])
			angle = Strategy().angleToPoint(pos, self.corner[0], self.corner[1])
			print("With the angle {} to reach destination.\n".format(angle))
			speed = 100

			if distanceDestination < 10:
				speed = max(min(100, self.robot.speed() / (10 - distanceDestination)), 1)

			self.robot.drive(angle, speed)

			if distanceDestination == 0:
				self.robot.drive(angle, 0)
				self.arrivalToCorner = True
		else:

			wide = 20
			detectedRobots = self.robot.scan(self.angleToScan, wide)
			print("I'm scanning with the angle {}\n".format(self.angleToScan))
			print("The number of detected robots is = {}.\n".format(detectedRobots))
			self.angleToScan = self.angleToScan + 20

			if self.angleToScan >= self.rangeToScan[1]:
				self.angleToScan = self.rangeToScan[0]

		# Get the updated robot's location
		pos = self.robot.location()

		# Send my updated position to my companions
		self.counter = 1
		while self.counter <= 4:
			if self.counter != self.id:
				robotProxy = self.robotsContainer.getProxy("robot"+str(self.counter))
				companion = drobots.RobotControllerCompletePrx.uncheckedCast(robotProxy)
				companion.position(pos, self.id)
			self.counter += 1


	def robotDestroyed(self, current = None):
		print("Defender robot {} has been destroyed".format(self.id))

	def position(self, pointTransmitter, idTransmitter, current = None):
		self.companions[idTransmitter] = pointTransmitter

	def detectorEnemies(self, idDetector, pointTransmitter, enemies, current = None):
		# The tuple detectorInfo contains the point and the enemies found by a detector
		self.detectorInfo = (pointTransmitter, enemies)

		# The detectors contains all detector's info
		self.detectors[idDetector] = self.detectorInfo

class RobotControllerAttacker(drobots.RobotControllerAttacker):
	def __init__(self, bot, id):
		self.robot = bot
		self.id = id
		self.enemies = 0
		self.robotsContainer = Functions().getContainer(1)
		self.companions = {}
		self.detectors = {}
		self.arrivalToCentre = False
		self.rangeToShoot = (0,360)
		self.angleToShoot = 0

		print("I'm the attacker robot {}. \n".format(self.id))

	def turn(self, current = None):
		print("Attacker robot {} turn. \n".format(self.id))
		
		# Get the robot's data
		pos = self.robot.location()
		energy = self.robot.energy()
		damage = self.robot.damage()

		if not self.arrivalToCentre:
			#We set the centre coordenates as we want the attacker to move to the centre
			coordenateX = 200
			coordenateY = 200
			distanceDestination = Strategy().distanceToPoint(pos, coordenateX, coordenateY)
			print("I'm moving to the center of the battlefield.")
			angle = Strategy().angleToPoint(pos, coordenateX, coordenateY)
			print("With the angle {} to reach destination\n".format(angle))
			speed = 100

			if distanceDestination < 10:
				speed = max(min(100, self.robot.speed() / (10 - distanceDestination)), 1)

			self.robot.drive(angle, speed)

			if distanceDestination == 0:
				self.robot.drive(angle, 0)
				self.arrivalToCentre = True
				print("Now, I'm in the centre. Let's start shooting!\n")
		else:

			self.angleToShoot = self.angleToShoot + 45

			if self.angleToShoot >= self.rangeToShoot[1]:
				self.angleToShoot = self.rangeToShoot[0]

			distanceToShoot = 100
			
			validShoot = self.robot.cannon(self.angleToShoot, distanceToShoot)

			if validshoot:
				print("Fine! The shoot has hurt at least one enemy!")
			else:
				print("Sorry, there were no enemies near...")


		# Get the updated robot's location
		pos = self.robot.location()

		# Send my updated position to my companions
		self.counter = 1
		while self.counter <= 4:
			if self.counter != self.id:
				robotProxy = self.robotsContainer.getProxy("robot"+str(self.counter))
				companion = drobots.RobotControllerCompletePrx.uncheckedCast(robotProxy)
				companion.position(pos, self.id)
			self.counter += 1



	def robotDestroyed(self, current = None):
		print("Attacker robot {} has been destroyed".format(self.id))

	def position(self, pointTransmitter, idTransmitter, current = None):
		self.companions[idTransmitter] = pointTransmitter

	def detectorEnemies(self, idDetector, pointTransmitter, enemies, current = None):
		# The tuple detectorInfo contain the point and the enemies found by a detector
		self.detectorInfo = (pointTransmitter, enemies)

		# The detectors contains all detector's info
		self.detectors[idDetector] = self.detectorInfo

class RobotControllerComplete(drobots.RobotControllerComplete):
	def __init__(self, bot, id):
		self.robot = bot
		self.id = id
		self.enemies = 0
		self.robotsContainer = Functions().getContainer(1)
		self.companions = {}
		self.detectors = {}
		self.selectedPoint = False
		self.arrivalToPoint = False
		self.destinationPoint = (0, 0)
		self.actuationAngle = 90

		print("I'm the complete robot {}. \n".format(self.id))

	def turn(self, current = None):
		print("Complete robot {} turn. \n".format(self.id))

		# Get the robot's data
		pos = self.robot.location()
		energy = self.robot.energy()
		damage = self.robot.damage()

		if not self.arrivalToPoint:
			#We want to move the complete robots to the middle point of each battlefield side, starting by the nearest
			if not self.selectedPoint:
				self.destinationPoint = Strategy().getNearestPoint(pos)
				self.selectedPoint = True


			distanceDestination = Strategy().distanceToPoint(pos, self.destinationPoint[0], self.destinationPoint[1])
			print("I'm moving to the center of the battlefield.")
			print("From the current position {} {}.".format(pos.x, pos.y))
			angle = Strategy().angleToPoint(pos, self.destinationPoint[0], self.destinationPoint[1])
			print("With the angle {} to reach destination\n".format(angle))
			speed = 100

			if distanceDestination < 10:
				speed = max(min(100, self.robot.speed() / (10 - distanceDestination)), 1)

			self.robot.drive(angle, speed)

			if distanceDestination == 0:
				self.robot.drive(angle, 0)
				self.arrivalToPoint = True

				#Once the destination is reached, we assign the next point taking into account by counterclockwise turning.
				#The valid angle for each point is also assigned.
				if(self.destinationPoint == (200, 0)):
					self.destinationPoint = (399, 200)
					self.actuationAngle = 180
				elif (self.destinationPoint == (399, 200)):
					self.destinationPoint = (200, 399)
					self.actuationAngle = 270
				elif(self.destinationPoint == (200, 399)):
					self.destinationPoint = (0, 200)
					self.actuationAngle = 0
				else:
					self.destinationPoint = (200, 0)
					self.actuationAngle = 90

		if self.arrivalToPoint:

			energy = self.robot.energy()
			wide = 20
			#If there's enough energy, it scans to see if there are enemies
			if energy > 10:
				detectedRobots = self.robot.scan(self.actuationAngle, wide)
				print("The number of detected robots are {}.\n").format(detectedRobots)

			#If there's enough energy, it shoots.
			if energy > 50:
				distanceToShoot = 50
				validshoot = self.robot.cannon(self.actuationAngle, distanceToShoot)

				if validshoot:
					print("Fine! The shoot has hurt at least one enemy!")
				else:
					print("Sorry, there were no enemies near...")
				#Only once it shoots, it moves to another point.
				self.arrivalToPoint = False


		# Get the updated robot's location
		pos = self.robot.location()

		# Send my updated position to my companions
		self.counter = 1
		while self.counter <= 4:
			if self.counter != self.id:
				robotProxy = self.robotsContainer.getProxy("robot"+str(self.counter))
				companion = drobots.RobotControllerCompletePrx.uncheckedCast(robotProxy)
				companion.position(pos, self.id)
			self.counter += 1


	def robotDestroyed(self, current = None):
		print("Complete robot {} has been destroyed".format(self.id))

	def position(self, pointTransmitter, idTransmitter, current = None):
		self.companions[idTransmitter] = pointTransmitter

	def detectorEnemies(self, idDetector, pointTransmitter, enemies, current = None):
		# The tuple detectorInfo contain the point and the enemies found by a detector
		self.detectorInfo = (pointTransmitter, enemies)

		# The detectors contains all detector's info
		self.detectors[idDetector] = self.detectorInfo

class DetectorController(drobots.DetectorController):
	def __init__(self, id):
		self.robotsContainer = Functions().getContainer(1)
		self.id = id

	def alert(self, pos, enemies, current = None):
		print("Eureka! The detector {} has found {} enemies in the point {}. \n".format(self.id, enemies, pos))

		# Send the number of the enemies to the companion robots
		self.counter = 1
		while self.counter <= 4:
			robotProxy = self.robotsContainer.getProxy("robot"+str(self.counter))
			companion = drobots.RobotControllerCompletePrx.uncheckedCast(robotProxy)
			companion.detectorEnemies(self.id, pos, enemies)
			self.counter += 1

class RobotControllerI(drobots.RobotFactory):
	def make(self, robot, id, current):
		if (robot.ice_isA("::drobots::Defender") and robot.ice_isA("::drobots::Attacker")):
			servant = RobotControllerComplete(robot, id)
		elif (robot.ice_isA("::drobots::Attacker")):
			servant = RobotControllerAttacker(robot, id)
		elif (robot.ice_isA("::drobots::Defender")):
			servant = RobotControllerDefender(robot, id)


		robotProxy = current.adapter.addWithUUID(servant)
		prx_id = robotProxy.ice_getIdentity()
		direct_prx = current.adapter.createDirectProxy(prx_id)
		robotProxy = drobots.RobotControllerPrx.uncheckedCast(robotProxy)
		print("Robot proxy: {} \n".format(robotProxy))
		return robotProxy

	def makeDetector(self, id, current):
		servant = DetectorController(id)
		detectorProxy = current.adapter.addWithUUID(servant)
		prx_id = detectorProxy.ice_getIdentity()
		direct_prx = current.adapter.createDirectProxy(prx_id)
		detectorProxy = drobots.DetectorControllerPrx.uncheckedCast(detectorProxy)
		print("Detector proxy: {} \n".format(detectorProxy))
		return detectorProxy

class Server(Ice.Application):
	def run(self, argv):
		broker = self.communicator()
		adapter = broker.createObjectAdapter("RobotFactoryAdapter")

		servant = RobotControllerI()
		proxyFactory = adapter.add(servant, broker.stringToIdentity("robotFactory"))
		print("I'm the factory: {} \n".format(proxyFactory))

		factory = drobots.RobotFactoryPrx.uncheckedCast(proxyFactory)

		factoriesContainer = Functions().getContainer(0)

		id = len(factoriesContainer.list()) + 1
		factoriesContainer.link("factory"+str(id), factory)

		sys.stdout.flush()

		adapter.activate()
		self.shutdownOnInterrupt()
		broker.waitForShutdown()

		return 0

sys.exit(Server().main(sys.argv))
