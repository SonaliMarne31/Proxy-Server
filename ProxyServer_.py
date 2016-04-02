from socket import *
import sys
from sys import *
import time
import thread
from threading import Thread, current_thread
import datetime
import os, sys

#For logging create a file in working directory
workingDir = os.path.dirname(os.path.abspath(__file__))
print 'WD :'+workingDir
LOGFILE = workingDir + "\log.txt"
MAX_SIZE = 4096


#This function checks is file is already in cache. If in cache, fetch
# If file not in cache get it from actual web server
def getFromProxy(tcpCliSock, addr, listeningPort):

    #Start the request timer
    startTime = time.time()
    print 'Received client connection from :',addr
    messageBeforeSplit = tcpCliSock.recv(MAX_SIZE)
    message = messageBeforeSplit.split()
    
    # Extract the filename from the given message
    print 'Message :',message

    #Check if message if empty. i.e. the request header (URL) is empty.
    #If yes, do not proceed
    if len(message) < 1:
        print 'No request Received... Try again later...'
    else:
        if message[1] == '/':
            print "No request" # Discussed with friend.
        else:

            #This block will get all the required elements from the request...
            requestType = message[0]
            print' Request type: '+requestType
            filename = message[1].partition("/")[2]
            fileExist = "false"
            filetouse = "/" + filename
            try:
                # Check whether the file exists in the cache
                f = open(filetouse[1:], "r")
                outputdata = f.readlines()
                print "F : ",f
                fileExist = "true"
                print 'File Exists in cache !! Fetching...'

                # ProxyServer finds a cache hit and generates a response message
                tcpCliSock.send("HTTP/1.0 200 OK\r\n")
                tcpCliSock.send("Content-Type:text/html\r\n")

                # Send the content of the requested file to the client
                finalData = ''
                for i in range(0, len(outputdata)):
                    finalData += outputdata[i] 
                dataSize = getsizeof(finalData)
                print 'DataSize: ',dataSize
                tcpCliSock.send(finalData)

                #Calculate response Time
                responseTime = time.time() - startTime
                #Generate the timestamp
                ts = time.time()
                timeStamp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
                print 'Start logging...'
                with open(LOGFILE,'a') as logger:
                    logger.write("Request TimeStamp :"+timeStamp+"\n")
                    logger.write("---------------------- NEW CLIENT REQUEST (CACHE) -------------------------- \n")
                    logger.write("Request Type: "+str(requestType)+"\n")
                    logger.write("Host Name: "+str(filename)+"\n")
                    logger.write("Local Port number: "+str(listeningPort)+"\n")
                    logger.write("Host Address: "+str(addr)+"\n")
                    logger.write("Request from client at "+str(addr)+ " processed in "+str(responseTime)+" Response DataSize: "+str(dataSize)+"\n")
                    logger.write("---------------------- REQUEST_ENDED -------------------------- \n")
                    logger.close()

                print 'Read from cache'

                # Error handling for file not found in cache
            except IOError:

                print 'File Exist: ', fileExist
                if fileExist == 'false':
                    print 'File not in cache... Fetching from actual web server...'
                    print 'Processing the client request...'
                    # Create a socket on the proxyserver
                    print 'Creating socket on proxyserver....'
                    proxy_socket = socket(AF_INET, SOCK_STREAM)
                    hostn = filename
                    print 'Host Name: ', hostn
                    try:
                        # Connect to the socket to port 80
                        proxy_socket.connect((hostn, 80))
                        print 'Socket connected to port 80 of the host',hostn

                        fileobj = proxy_socket.makefile('r', 0)
                        fileobj.write("GET " + "http://" + filename + " HTTP/1.0\n\n")

                        # Read the response into buffer
                        buff = fileobj.readlines() 
                        dataSize = getsizeof(len(buff))

                        #Calculate the request response time
                        responseTime = time.time() - startTime
                        #Generate the timestamp
                        ts = time.time()
                        timeStamp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
                        #Creating logs
                        print 'Start logging...'
                        with open(LOGFILE,'a') as logger:
                            logger.write("Request TimeStamp :"+timeStamp+"\n")
                            logger.write("---------------------- NEW CLIENT REQUEST (NON CACHE) -------------------------- \n")
                            logger.write("Request Type: "+str(requestType)+"\n")
                            logger.write("Host Name: "+str(filename)+"\n")
                            logger.write("Local Port number: "+str(listeningPort)+"\n")
                            logger.write("Host Address: "+str(addr)+"\n")
                            logger.write("Request from client at "+str(addr)+ " processed in "+str(responseTime)+" Response DataSize: "+str(dataSize)+"\n")
                            logger.write("---------------------- REQUEST_ENDED -------------------------- \n")
                            logger.close()
                        # Create a new file in the cache for the requested file.
                        # Also send the response in the buffer to client socket
                        # and the corresponding file in the cache
                        #tmpFile = open(filename, 'w')
                        tmpFile = open("./" + filename,"wb")
                        for i in range(0, len(buff)):
                            tmpFile.write(buff[i])
                            tcpCliSock.send(buff[i])
                        
                        #Close all sockets and files that are open
                        tmpFile.close()
                        tcpCliSock.close()
                        proxy_socket.close()
                    except:
                        #Illegal request do not process
                        print 'Illegal request'

                else:
                    # HTTP response message for file not found
                    # Do stuff here
                    #Add error to logs
                    logger = open(LOGFILE, 'a')
                    logger.write("HTTP/1.0 404 Not Found\r\n the address " + filename)
                    tcpCliSock.send("HTTP/1.0 404 Not Found\r\n")
                    
    # Close the socket and the server sockets
    tcpCliSock.close()



def initialize():    
    
    if len(sys.argv) < 1:
        print 'Usage: "python ProxyServer.py server_ip"\n[server_ip : It is the IP Address of the Proxy Server'
        sys.exit(2)

    # Create a server socket, bind it to a port and start listening
    # sys.argv contains the argument list entered by the user, 1 is port number.
    listeningPort = raw_input("Please enter the port number: ")
    if len(listeningPort) < 4:
        listeningPort = 8080
    else:
        listeningPort = int(listeningPort)
    print "Listening port number is :", listeningPort
    print "Creating a socket...."

    # Create a server socket
    try:
        tcpSerSock = socket(AF_INET, SOCK_STREAM)
        print 'Socket created successfully...'
    except socket.error as socketErr:
        print 'Error creating socket...'
        sys.exit(2)

    #Bind to server socket    
    tcpSerSock.bind(('', listeningPort))
    #listening to server socket
    tcpSerSock.listen(5)
    print 'Binded to server socket...'
    while 1:
        # Start receiving data from the client
        print 'Now Server ready to serve...'
        tcpCliSock, addr = tcpSerSock.accept()
    
        #create a new  thread for each new request
        thread.start_new_thread(getFromProxy,(tcpCliSock, addr, listeningPort))
    tcpSerSock.close()


def main():
    initialize();

if __name__ == "__main__":
    main()