#!/usr/bin/python3
# imports
import socket 
import array
import sys
import pickle
import threading
import params


global host, port

#host and port for server
host='localhost'
port=params.serv_port

# list to maintain peerID to its port list
global peer_port_list
peer_port_list=[] #index=peerID : port ;;;int pair

# dictionary to hold filelist (values) and peerID (key)
global fileDict
fileDict={}		#"peerID":file1,file2...


#Initial setup to allot peerID to the new client
# retuns -1 if connection breaks
# otherwise returns the alloted peerID
# if peerID already exists then, that ID is returned
def do_handshake(client):
	try:
		data_in=pickle.loads(client.recv(1024))
	except:
		return -1
	peerID= data_in[0]
	peer_port= data_in[1]
	# new peerID allotment
	if peerID==-1:						
		peer_port_list.append(peer_port)
		try:
			client.sendall(pickle.dumps((len(peer_port_list)-1)))
		except:
			return -1
		return (len(peer_port_list)-1)
	# old connection, peerID from list
	else:
		peer_port_list[peerID]=peer_port
		try:
			client.sendall(pickle.dumps(peerID))
		except:
			return -1
		return peerID
#function to save file list of a particular peer against peerID (as key)
#temp is used to control print statements
# returns False if connection breaks or invalid response
#otherwise true
def filelistRegister(client, data_in, temp):
	global fileDict

	data_split=data_in.split(':')
	peerID=data_split[1]
	fileName=data_split[2]
	for i in range(3,len(data_split)):
		fileName+=":"
		fileName+=data_split[i]

	#create new key value pair
	if peerID not in fileDict:
		fileDict[peerID]=[]
	#append value list if file is not already there
	if fileName not in fileDict[peerID]:
		fileDict[peerID].append(fileName)

	if temp:
		print(">>Client {} is adding file to its file list".format(peerID))
	if fileName!="":
		print("   >File:", fileName)
	# reply to client 
	try:
		client.sendall(pickle.dumps("DONE"))
	except:
		return False
	return True
# function to delete the file list against the supplied peer ID
def file_DEregister(peerID):
	#check if key is available
	if str(peerID) in fileDict:
		del fileDict[str(peerID)]
		print("->File list of Client {} removed.".format(peerID))

#function to a search file from dictionary
# returns false if connection breaks or invalid response
# otherwise returns true  
# sends peerID of client having file
def fileSearch(client, data_in):
	global fileDict
	data_split=data_in.split(':')
	peerID=data_split[1]
	fileName=data_split[2]
	for i in range(3,len(data_split)):
		fileName+=":"
		fileName+=data_split[i]
	print(">>Client {} queried file named {}.".format(peerID,fileName))

	fileFound=[]
	#finding file and appending peerID and port of file holder to a list
	for pID,files in fileDict.items():
		for file in files:
			if file==fileName and pID!=peerID:
				fileFound.append((pID,str(peer_port_list[int(pID)])))
	

	#if file is not found
	if fileFound==[]:	
		print(">>File {} queried by client {} is not available at any of the peers.".format(fileName,peerID))
		try:
			client.sendall(pickle.dumps("-1"))
		except:
			return False
	# if found the each peerID and Port pair is sent to client indivisually.	
	else:
		print(">>Queried file {} by Client {} is available.".format(fileName,peerID))
		for pID, portpID in fileFound:
			print("   > @",pID)
			data_out=pID+":"+portpID
			try:
				client.sendall(pickle.dumps(data_out))
			except:
				return False

			try:
				if pickle.loads(client.recv(4096))!="DONE":
					return False
			except:
				return False

	#To mark end of list
		try:
			client.sendall(pickle.dumps("-2"))
		except:
			return False
	return True


#function called by the thread to handle incoming cnnections
def handleClient(client):
	# get peerID of the new client
	peerID=do_handshake(client)
	if peerID==-1:
		print("###Problem with request from a new Client...Disconnecting the client.")
		client.close()
		return

	print("***New client connected with peer ID = {}".format(peerID))
	temp=True
	while True:
		# get command
		try:
			data_in=pickle.loads(client.recv(4096))
		except:
			break
		# case when client wants to disconnect.
		if data_in[0:4]=="EXIT":
			break
		#case when client to register file list 
		elif data_in[0:8]=="REGISTER":
			if filelistRegister(client, data_in, temp)==False:
				break
			temp=False
		# case when client wants to lookup
		elif data_in[0:6]=="SEARCH":
			if fileSearch(client, data_in)==False:
				break
			temp=True
		# incase of protocol violation
		else:
			break
	

	print("***Client with ID {} requested unknown service...Disconnecting the client.".format(peerID))
	#removing file list from dictionary
	file_DEregister(peerID)
	client.close()
	return



# main function
def main():
	s = socket.socket() 
	try:
		s.bind((host, port))
		print("->Server up.")
	except:
		raise SystemExit('->Server cannot start. Please check port.')
	while True: 
		s.listen(5)
		client, addr = s.accept()
		# new thread for every connection
		threading.Thread(target=handleClient, args=(client,)).start()  


if __name__ == '__main__':
	 main()