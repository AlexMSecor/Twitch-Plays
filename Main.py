import socket
from dotenv import load_dotenv
import os
from emoji import demojize
import re

# Load environment variables
load_dotenv()
server = 'irc.chat.twitch.tv'
port = 6667
nickname = os.getenv('TWITCH_NICKNAME')
token = os.getenv('TWITCH_OAUTH')
channel = '#' + input("Enter the channel name: ")

# Create and connect the socket
sock = socket.socket()
try:
    sock.connect((server, port))
except socket.error as e:
    print(f"Error connecting to server: {e}")
    exit(1)

# Authenticate and join the channel
sock.send(f"PASS {token}\n".encode('utf-8'))
sock.send(f"NICK {nickname}\n".encode('utf-8'))
sock.send(f"JOIN {channel}\n".encode('utf-8'))

while True:
    # Receive server response
    resp = sock.recv(2048).decode('utf-8')
    
    if len(resp) > 0:
        # Get the original message
        msg = demojize(resp)
        
        # Get and print the username, channel, and message
        match = re.search(r':(.*?)!(.*?)@(.*?)\.tmi\.twitch\.tv PRIVMSG #(.*?) :(.*)', msg)
        
        if match:
            # Extract the username, channel, and message
            username = match.group(1)
            message = match.group(5)
            print(f"Username: {username}")
            print(f"Message: {message}")
        else:
            print("Message cannot be displayed.")

        print ("\n")
