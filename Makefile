.DEFAULT: help
help:
	@echo "make get-dev"
	@echo "      install python 3.5 and python3-pip"
	@echo "make server"
	@echo "       run server"
	@echo "make peer_1"
	@echo "       run peer_1"
	@echo "make peer_2"
	@echo "       run peer_2"
	@echo "make peer_3"
	@echo "       run peer_3"


get-dev:
	sudo apt-get -y install python3.5 python3-pip

server:
	python3 server.py
peer_1:
	python3 peer_1.py
peer_2:
	python3 peer_2.py
peer_3:
	python3 peer_3.py

