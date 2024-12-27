# TODO: Clean up imports
import socket
from dotenv import load_dotenv
import os
import re
import pandas as pd
import time
import itertools
import threading
import keyboard
import json

# Constants
DEFAULT_DURATION_TIME = 60
DEFAULT_CONTROLS = ["left", "right", "up", "down"]
TWITCH_SERVER = 'irc.chat.twitch.tv'
TWITCH_PORT = 6667

# Load environment variables from .env file
def load_environment_variables():
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
def loading_animation(event, available_controls_length):
    loading_states = itertools.cycle([".", "..", "..."])
    while not event.is_set():
        print(f"\rGetting top {available_controls_length} words{next(loading_states)}", end = "")
        time.sleep(0.5)
    print(f"\rGetting top {available_controls_length} words... Done!")

# Continuously reads messages from Twitch chat and executes actions for words in the control_map
def handle_realtime_actions(sock, control_map):
    print("Listening for messages...")
    # TODO: Add a way to pause the execution
    try:
        while True:
            resp = sock.recv(2048).decode('utf-8')
            matches = re.findall(r':(.*?)!.*?@.*?\.tmi\.twitch\.tv PRIVMSG #(.*?) :(.*)', resp)
            if matches:
                for username, channel, message in matches:
                    words = message.split()
                    for word in words:
                        if word in control_map:
                            key = control_map[word]
                            print(f"Executing action for word '{word}' -> key '{key}'")
                            # TODO: I think this gets caught up and it doesn't register the key press, needs further testing
                            keyboard.press_and_release(key)
    except KeyboardInterrupt:
        print("\nStopped listening for messages.")

# Function to collect words and update DataFrame
def collect_words(sock, available_controls_length, duration = None):
    duration = duration or DEFAULT_DURATION_TIME
    word_df = pd.DataFrame(columns=["word", "count"])
    end_time = time.time() + duration
    while time.time() < end_time:
        resp = sock.recv(2048).decode('utf-8')
        matches = re.findall(r':(.*?)!.*?@.*?\.tmi\.twitch\.tv PRIVMSG #(.*?) :(.*)', resp)
        if matches:
            for username, channel, message in matches:
                words = message.lower().split()
                for word in words:
                    if word in word_df["word"].values:
                        word_df.loc[word_df["word"] == word, "count"] += 1
                    else:
                        word_df = pd.concat([word_df, pd.DataFrame({"word": [word], "count": [1]})], ignore_index = True)

    # Sort by count and get the top 5 words
    return word_df.sort_values(by = "count", ascending = False).head(available_controls_length)

def create_control_map(top_words, available_controls):
    control_map = {}
    for word, key in zip(top_words, available_controls):
        control_map[word] = key
    return control_map

def load_settings():
    with open("settings.json", "r") as file:
        settings = json.load(file)
    return {
        "duration": settings.get("duration", DEFAULT_DURATION_TIME),
        "controls": settings.get("controls", DEFAULT_CONTROLS)
    }

# Main function
def main():
    try:
        # Load settings.json file
        duration, available_controls = load_settings().values()

        # Get Twitch credentials to connect to the chat
        nickname, token = load_environment_variables()
        channel = '#' + input("Enter the channel name: ").strip()
        sock = connect_to_twitch(TWITCH_SERVER, TWITCH_PORT, nickname, token, channel)

        # Event to control the loading animation
        stop_event = threading.Event()
        # Start the loading animation in a separate thread
        loading_thread = threading.Thread(target = loading_animation, args = (stop_event,len(available_controls),))
        loading_thread.start()

        # Collect words for the specified duration
        if duration == 0:
            word_df = collect_words(sock, len(available_controls))
        else:
            word_df = collect_words(sock, len(available_controls), duration)

        # Stop the loading animation
        stop_event.set()
        loading_thread.join()

        # Display the results
        print(f"\n=== Top {len(available_controls)} Words Collected ===")
        print(word_df.reset_index(drop = True))

        # Create a word map with actions
        control_map = create_control_map(word_df["word"].tolist()[:len(available_controls)], available_controls)

        # Display the word map
        print("\n=== Control Map ===")
        print(f"Generated control map: {control_map}")

        print("Load the game and press 'Enter' to start listening for messages.")
        input()

        print("Switch to the game window!")
        # Five seconds delay to switch to the game window
        time.sleep(5)

        # Start listening for messages and execute actions
        # TODO: This stops after so long, need to find a way to keep it running
        handle_realtime_actions(sock, control_map)
    except Exception as e:
        print("An error occurred: ", e)

# Entry point
if __name__ == "__main__":
    main()
