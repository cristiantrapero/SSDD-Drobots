#!/usr/bin/make
# -*- mode:makefile -*-

SERVIDOR=drobots

all: factoriesContainer robotsContainer factories run

factoriesContainer:
	gnome-terminal --tab -e "python Container.py --Ice.Config=./configurations/factoriesContainer.config"

robotsContainer:
	gnome-terminal --tab -e "python Container.py --Ice.Config=./configurations/robotsContainer.config"

factories:
	gnome-terminal --tab -e "python Factory.py --Ice.Config=./configurations/factory1.config"
	gnome-terminal --tab -e "python Factory.py --Ice.Config=./configurations/factory2.config"
	gnome-terminal --tab -e "python Factory.py --Ice.Config=./configurations/factory3.config"

run:
	@read -p "Introduce the number of the server you want to connect to: " number; \
	python Client.py --Ice.Config=./configurations/drobots.config $(SERVIDOR)$$number Cristian
