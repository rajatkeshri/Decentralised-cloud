#!/usr/bin/python3
#imports
import socket 
import array
import os
import os.path
import sys
import pickle
import glob
import threading
import time
import params


global host, port, portP
#host and port pair to connect to server
host='localhost'
port=params.serv_port

# port for other peer to connect to it
portP=params.peer_3_port

global shared_dirPath
# relative path (to project) to shared directory 
shared_dirPath=params.peer_3_path

global peerID
# ID of this client
peerID=-1


#Funciton to initiate communication
# returns False if connection break or violation
# otherwise returns true with updating peerID
def handshake_server(s):
	global peerID
	data_out=[peerID,portP]
	try:
		s.sendall(pickle.dumps(data_out))
	except:
		return False
	try:
		#update peerID global variable
		peerID=pickle.loads(s.recv(1024))
	except:
		return False
	return True

#function returns filelist in the shared directory
def get_fileList(dirPath):
	fileList= [os.path.basename(x) for x in glob.glob(dirPath)]			######change path#####
	return fileList

#function to send filelsit to server
#it works recursively
# returns False if connection break or violation
# otherwise returns true
def send_fileList(s):
	fileList=get_fileList(shared_dirPath)
	for fileName in fileList:
		#create object to send
		data_out="REGISTER:"+str(peerID)+":"+fileName
		try:
			s.sendall(pickle.dumps(data_out))
		except:
			return False
		try:
			#wait for response
			if pickle.loads(s.recv(1024))!="DONE":
				return False

		except:
			return False

	return True

#Function to handle upload request
#closes connection if connection breaks or response protocol violation
#uploads file upon the request from peer
def upload_file(client):
	donef=True
	try:
		#wait for response
		data_in=pickle.loads(client.recv(4096))
	except:
		print("\n->Problem with request from a new Client...Disconnecting the client.")
		print(">>Please enter the file needed: ") 

		client.close()
		return
	try:
		#create data from response from object
		data_split=data_in.split(':')
		cmd=data_split[0]
		pID=data_split[1]
		fileName=data_split[2]
		for i in range(3,len(data_split)):
			fileName+=":"
			fileName+=data_split[i]
	except:
		print("\n->Client requested unknown service...Disconnecting the client.")
		print(">>Please enter the file needed: ") 
		client.close()
		return

	#if protocol is OBATAIN
	if cmd=="OBTAIN":
		print("\n>>File {} requested by client {}.".format(pID,fileName))

		#check if file is avialable
		if fileName in get_fileList(shared_dirPath):
			try:
				#if available, then send response
				client.sendall(pickle.dumps("True"))
			except:
				print("->Problem with request from the Client...Disconnecting the client.")
				client.close()
				return


			print(">>File {} requested by  client {} is available and preparing to send.".format(fileName,pID))
			#get file path
			filePath=shared_dirPath[:-1]+"/"+fileName
			#open file
			f = open(filePath,'rb')
			#read file and send over the network
			l = f.read(1024)
			while l:
					try:
						client.sendall(l)
					except:
						donef=False
						break
					l = f.read(1024)
			f.close()
			#if file is sent, close connection
			if donef==True:
				client.shutdown(socket.SHUT_WR)
				print(">>File {} requested by client {} was sent.".format(fileName,pID))
			#if any problem then, close connection and print details
			else:
				print(">>File {} requested by client {} could not be sent.".format(fileName,pID))


		#if file is not available
		else:

			client.sendall(pickle.dumps("False"))
			print("File {} requested by client {} is not available.".format(fileName,pID))
	#invalid response
	else:
		print("\n->Client requested unknown service...Disconnecting the client.")
		print(">>Please enter the file needed: ") 

		client.close()
		return
	
	print("->Disconnecting client with ID ", pID)
	print(">>Please enter the file needed: ") 

	client.close()


#Function to start inter peer comunication server
# handles each client inseperate thread
#exist if server is not up or ctrl+c
def upload_server():
	s_up = socket.socket()
	try:
	
		s_up.bind((host, portP))

	except:
		print('->Upload server could not start. Exiting.')
		raise
		return

	print("->Upload server is now running at port", portP)
	while True:
		try:
			s_up.listen(5)               
			client, addr = s_up.accept()
		except KeyboardInterrupt:
			s_up.close()
		#thread to handle each client
		threading.Thread(target=upload_file, args=(client,)).start()

#function to download file from a peer
#returns false if fail
#otherwise return true	
# at the end update the file list
def downloadFile(port_s, fileName, s):
	s_p = socket.socket()	
	try:
		#connect to peer holding file
		s_p.connect((host, port_s))
	except:
		print("###Peer is not available. Try other peers or try later.")
		return False
	#create data object 
	data_out= "OBTAIN:"+str(peerID)+":"+fileName
	try:
		#send data object
		s_p.sendall(pickle.dumps(data_out))
	except:
		print("###Peer is not available. Try other peers or try later.")
		return False
	
	try:
		#check the response for data availability
		if pickle.loads(s_p.recv(1024))=="False":
			print("###Peer is not available. Try other peers or try later.")
			return False
	except:
		print("###Peer is not available. Try other peers or try later.")
		return False

	print(">>Downloading file {}.".format(fileName))
	#get file list in shared directory

	fList= get_fileList(shared_dirPath)
	#If file is available in directory then, rename it
	temp=True
	while True:
		if fileName in fList:
			if temp:
				print("->File exist in shared directory. Renaming...")
				temp=False
			fileName = '1'+fileName
		else:
			break
	temp=True

	#get file path
	filePath_f=shared_dirPath[:-1]+"/"+fileName
	#open file
	fileNew = open(filePath_f,'wb')
	#get the file from peer server and write to it
	try:
		filePart = s_p.recv(1024)
		while filePart:
			fileNew.write(filePart)
			filePart = s_p.recv(1024)
	except:
		print("###File couldn't be downloaded. Try again.")
		return False
	fileNew.close()
	print("->Downloaded. Updating indexing server")
	#update file list in indexing server.
	if send_fileList(s):
		print("->Updated")
	else:
		raise SystemExit('###Link to server failed, please try again later.')

	return True
	








#Function to handle peer and indexing server communication
# ALso it works with user input
# Exits if connection breaks.
def server_talk(s):
	global peerID

	while True:
		#get user input 
		try:
			user_fileName= input(">Please enter the file needed: ")
		except KeyboardInterrupt:
			s.sendall(pickle.dumps("EXIT"))	
			s.close()
			return
		# create object to send over network
		data_out="SEARCH:"+str(peerID)+":"+user_fileName

		#sending
		try:
			s.sendall(pickle.dumps(data_out))
		except:
			raise SystemExit('Link to the server failed.')

		#wait for the response
		data_in=""
		try:
			data_in=pickle.loads(s.recv(4096))
		except:
			raise SystemExit('Link to the server failed.')


		#if file is not found
		if data_in=="-1":
			print("*File not found in any of the active peers. Try again later.")
		#file found
		else:
			file_info={}
			print("*File found in active peers.")
			#loops until list of all peer having the file returned
			while data_in!="-2":
				data_split=data_in.split(':') #pID,portID

				file_info[data_split[0]]=data_split[1]
				
	
				
				print("> file@ peerID:",data_split[0])
				#return response
				try:
					s.sendall(pickle.dumps("DONE"))
				except:
					raise SystemExit('Link to the server failed.')
				#wait for more data
				try:
					data_in=pickle.loads(s.recv(4096))
				except:
					raise SystemExit('Link to the server failed.')

			cnt=0
			while cnt<3:
				#wait for user to select file
				try:
					sel=input(">Enter peerID to select peer (Enter cancel to cancel): ")
				except KeyboardInterrupt:
					s.close()
					raise
				if sel=="cancel":
					break
				#if proper selection then call function to download file
				if sel in file_info:
					downloadFile(int(file_info[sel]), user_fileName,s)
					break
				#give 3 tries 
				else:
					print("Wrong selection> Try again.")
					cnt+=1

		
#main function
#connects to server and starts a seperate thread for upload server
#Also starts a new thread for user to index server interaction
# exits if connection fails.
def main():

	s = socket.socket()

	try:                
		s.connect((host, port))
		print("->Connected to the server at port", port)
	except:
		raise SystemExit('->Server is down, please try again later.')

	#funtion call to update global peerID 
	if handshake_server(s):
		print("***Connection successfull (peerID= {}). Syncing shared folder file list.".format(peerID))
	else:
		raise SystemExit('->Link to server failed, please try again later.')
	
	#function call to update peer list
	if send_fileList(s):
		print("->File list is synced.")
	else:
		raise SystemExit('->Link to server failed, please try again later.')

	#thread for inter peer communication
	threading.Thread(target=upload_server).start()
	time.sleep(1) 
	#thread for inter peer and indexing server communication
	threading.Thread(target=server_talk, args=(s,)).start()


if __name__ == '__main__':
	main()