# -*- coding: utf-8 -*-
"""
Created on Sat Oct 19 20:51:39 2024

@author: Isabella Crowe & Raymi Vargas
Univeristy: Wentworth Istitute of Technology
Professor: Salem Othman
Final Project: Super Chat Room
        
"""

import socket
import threading

# Connection Data
host = '127.0.0.1'
port = 8081
buffer_size = 1028

# Starting Server
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host, port))
server.listen()

# Lists For Clients and Their Nicknames
clients = []
nicknames = []


def broadcast(message):         
    for client in clients:      # Iterates through the clients in the collection of 'clients'
        client.send(message)    # Sends the message to the current clients


def handle(client):     # Keep the connection open while listening the incoming message
    
    while True:
        
        try:            
                       
            message = client.recv(buffer_size)  # .recv(buffer_size) get the message sent by the client
            print(f"{nicknames[clients.index(client)]} says {message}") # prints the message to the concole.
            broadcast(message)  # Broadcast it to the other clients
        
        except:     # Handles the situation when an error occurs (or if a client disconnects)
          
            index = clients.index(client) # find the client(s) index in the chat to acurrently follow the next lines on code
            clients.remove(client) # removes the client
            client.close() # closes the connection to the client. 
            nickname = nicknames[index] # gets the nickname of the client when leaving
            broadcast('{} left!'.format(nickname).encode('ascii')) # Broadcast the message the clieint has left in the chat
            nicknames.remove(nickname) # removes the client after logging out
            break


def receive():
    while True: 
        
      
        client, address = server.accept() # server.accept() waits for the connection from tne client(s)
        print("Connected with {}".format(str(address))) # Prints the address of the client(s) that have connected to the server

        
        client.send('NICK'.encode('ascii')) # Request And Store Nickname. 
                                            # If no NICK is given you are asked for one
                                            # Encodes the nickname
        nickname = client.recv(buffer_size).decode('ascii') # Recieves and decodes the nickname
                                                            # client.recv(buffer_size) recieves the clients responce
                                                            # decoded from  ascii  to string and stored as a varible
        nicknames.append(nickname) # Stores nicknames in a object
        clients.append(client) # The nickname is added the the 'nickname' list. 

       
        print("Name is {}".format(nickname))  # Prints out your name (debugging)
        broadcast("{} joined! \n".format(nickname).encode('ascii')) # Broad cast it to all the other clients
        client.send('You are Connected to server!'.encode('ascii')) # Sends a comfirmation messages to the clients as they log in.

        # Start Handling Thread For Client
        thread = threading.Thread(target=handle, args=(client,))
        thread.start()
            
        
print('The Server running ----->') # Shows that the server is running
receive()