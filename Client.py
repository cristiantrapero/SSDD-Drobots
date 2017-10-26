#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import Ice
import socket
Ice.loadSlice('factory.ice --all -I .')
import drobots
Ice.loadSlice('container.ice --all -I .')
import Services

class PlayerI(drobots.Player):
	def __init__(self, broker, my_IP, robotsContainer):
		self.broker = broker
		self.my_IP = my_IP
		self.robotsContainer = robotsContainer

		# Aditional variable to get the different factories
		# The number 2 is due to the assigned port in the configuration
		self.portCounter = 2

	def win(self, current):
		print("You win the game. \n")
		current.adapter.getCommunicator().shutdown()

	def lose(self, current):
		print("You lose the game. \n")
		current.adapter.getCommunicator().shutdown()

	def gameAbort(self, current):
		print("Aborted game. \n")
		current.adapter.getCommunicator().shutdown()

	def makeController(self, robot, current = None):
		print("Creating robot. \n")

		# The first factory contains 2 robots
		if self.portCounter == 5 :
			self.portCounter = 2

		proxyFactory = self.broker.stringToProxy("robotFactory -t -e 1.1:tcp -h {} -p 909{} -t 60000".format(self.my_IP, self.portCounter))
		self.portCounter += 1

		# Recover the factory to add the robot controller
		factory = drobots.RobotFactoryPrx.checkedCast(proxyFactory)

		# Calculate the id of the robot based on the number of robots the container has
		id = len(self.robotsContainer.list()) + 1

		# Get the robot proxy
		robotProxy = factory.make(robot, id)

		# Add the robot proxy to the robot container
		self.robotsContainer.link("robot"+str(id), robotProxy)

		return robotProxy

	def makeDetectorController(self, current):
		print ("Detector connected. \n")

		if self.portCounter == 5 :
			self.portCounter = 2

		proxyFactory = self.broker.stringToProxy("robotFactory -t -e 1.1:tcp -h {} -p 909{} -t 60000".format(self.my_IP, self.portCounter))
		self.portCounter +=1

		# Recover the factory to add the robot controller
		factory = drobots.RobotFactoryPrx.checkedCast(proxyFactory)

		# Calculate the id of the detector, minus 3 due to id of robots
		id = len(self.robotsContainer.list()) - 3

		detectorProxy = factory.makeDetector(id)

		self.robotsContainer.link("detector"+str(id), detectorProxy)

		return detectorProxy

class Cliente(Ice.Application):
	def getIP(self, current = None):
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		s.connect(("atclab.esi.uclm.es",80))
		ip = s.getsockname()[0]
		s.close()
		return ip

	def getRobotsContainer(self, my_IP, containerPort, current = None):
		broker = self.communicator()
		proxyRobotsContainer = broker.stringToProxy("container1 -t -e 1.1:tcp -h {} -p 909{} -t 60000".format(my_IP, containerPort))
		robotsContainer = Services.ContainerPrx.checkedCast(proxyRobotsContainer)
		return robotsContainer

	def run(self, argv):
		broker = self.communicator()
		adapter = broker.createObjectAdapter("PlayerAdapter")
		adapter.activate()

		proxy_game = broker.stringToProxy(argv[1])

		try:
			# Connect to the game server
			game = drobots.GamePrx.checkedCast(proxy_game)

		except Ice.DNSException:
			print("You must connect to the UCLM's VPN to run the programm.\n")
			return 1

		if game is None:
			print ("Game proxy invalid.\n")
			return 1

		# Get the robots container
		my_IP = self.getIP()
		robotsContainer = self.getRobotsContainer(my_IP, 1)

		servant = PlayerI(broker, my_IP, robotsContainer)

		my_proxy = adapter.addWithUUID(servant)
		my_proxy = drobots.PlayerPrx.uncheckedCast(my_proxy)

		try:
			game.login(my_proxy, argv[2])
			print("\nLogged into the server {} with the nick {}. \n".format(argv[1], argv[2]))

		except drobots.GameInProgress:
			print("Game in progress. Try with other. \n")
			return 1

		except drobots.InvalidProxy:
			print("Invalid proxy.\n")
			return 1

		except drobots.InvalidName, razon:
			print("Invalid nickname. Try with other. \n")
			return 1

		self.shutdownOnInterrupt()
		broker.waitForShutdown()

		return 0

sys.exit(Cliente().main(sys.argv))
