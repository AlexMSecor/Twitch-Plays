import socket
from dotenv import load_dotenv
import os
import re
import pandas as pd
import time
import itertools
import threading

# Constants
DEFAULT_DURATION_TIME = 60

# Initialize a DataFrame to track word counts
word_df = pd.DataFrame(columns = ["word", "count"])

# Load environment variables from .env file
def load_environment_variabes():
    load_dotenv()
    nickname = os.getenv('TWITCH_NICKNAME')
    token = os.getenv('TWITCH_OAUTH')
    return nickname, token

# Connect to Twitch with the given credentials
def connect_to_twitch(server, port, nickname, token, channel):
    sock = socket.socket()
    sock.connect((server, port))
    sock.send(f"PASS {token}\n".encode('utf-8'))
    sock.send(f"NICK {nickname}\n".encode('utf-8'))
    sock.send(f"JOIN {channel}\n".encode('utf-8'))
    return sock

# Loading animation function
def loading_animation(event):
    loading_states = itertools.cycle([".", "..", "..."])
    while not event.is_set():
        print(f"\rGetting top 10 words{next(loading_states)}", end = "")
        time.sleep(0.5)
    print("\rGetting top 10 words... Done!")

# Function to collect words and update DataFrame
def collect_words(sock, duration = DEFAULT_DURATION_TIME):
    global word_df
    end_time = time.time() + duration
    while time.time() < end_time:
        resp = sock.recv(2048).decode('utf-8')
        matches = re.findall(r':(.*?)!.*?@.*?\.tmi\.twitch\.tv PRIVMSG #(.*?) :(.*)', resp)
        if matches:
            for username, channel, message in matches:
                words = message.split()
                for word in words:
                    if word in word_df["word"].values:
                        word_df.loc[word_df["word"] == word, "count"] += 1
                    else:
                        word_df = pd.concat([word_df, pd.DataFrame({"word": [word], "count": [1]})], ignore_index = True)

    # Sort by count and get the top 10 words
    word_df = word_df.sort_values(by = "count", ascending = False).head(10)

# Main function
def main():
    server = 'irc.chat.twitch.tv'
    port = 6667
    nickname, token = load_environment_variabes()
    channel = '#' + input("Enter the channel name: ")
    sock = connect_to_twitch(server, port, nickname, token, channel)

    # Event to control the loading animation
    stop_event = threading.Event()

    # Start the loading animation in a separate thread
    loading_thread = threading.Thread(target = loading_animation, args = (stop_event,))
    loading_thread.start()

    # Collect words for the specified duration
    collect_words(sock)

    # Stop the loading animation
    stop_event.set()
    loading_thread.join()

    # Display the results
    print("\n=== Top 10 Words in the Last Minute ===")
    print(word_df.reset_index(drop = True))

# Entry point
if __name__ == "__main__":
    main()
