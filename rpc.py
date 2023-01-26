#!/usr/bin/env python3
"""
https://github.com/its-ag/discord-rpc
"""

import sys
import time
import base64

import gi
gi.require_version('Playerctl', '2.0')
from gi.repository import Playerctl, GLib
from pypresence import Presence
from colorama import init, Fore
import pypresence.exceptions
import requests

manager = Playerctl.PlayerManager()

print("Starting RPC client...")
def pp():
    print(f"""
    {Fore.WHITE}----------------------------------------
        {Fore.RED}Developer: {Fore.BLUE}its-ag
        {Fore.RED}Discord: {Fore.BLUE}Arunava#1288
    {Fore.WHITE}----------------------------------------
    """)
pp()
RPC = Presence('987287937467170846') # I am to lazy to upload my own assets

def get_time():
    return time.time()*1000             # Get current timestamp (s)
last_switch = get_time()
last_image = None
last_image_link = "music"
last_track = None

def connect_rpc():
    while True:
        try:
            RPC.connect()
            print("RPC client connected")
            break
        except ConnectionRefusedError as e:
            print("Failed to connect to RPC! Trying again in 10 seconds...")
            time.sleep(10)
        except (FileNotFoundError, AttributeError) as e:
            print("RPC failed to connect due to Discord not being opened yet. Please open it. Reconnecting in 10 seconds...")
            time.sleep(10)

def setup_player(name):
    player = Playerctl.Player.new_from_name(name)
    player.connect('playback-status::playing', on_play, manager)
    player.connect('playback-status::paused', on_pause, manager)
    player.connect('metadata', on_metadata, manager)
    player.connect('seeked', on_seeked, manager)
    manager.manage_player(player)
    update(player)

def get_song(player):
    return "%s - %s" % (player.get_title(), player.get_artist())

def get_timestamps(player):
    now = get_time()
    # Get length of song (us)
    try:
        length = int(player.print_metadata_prop('mpris:length'))/1000
    except TypeError as e:
        length = None
    try:
        pos = player.get_position()/1000    # Get position (us)
    except gi.repository.GLib.Error as e:
        pos = None
    if pos is not None and length is not None:
        start = now-pos
        return (start, start+length)
    global last_switch, last_track
    cur_title = player.get_title()
    if cur_title != last_track:
        last_track = cur_title
        last_switch = now
    return (last_switch, None)

def update(player):
    status = player.get_property('status')
    try:
        if status == "":
            RPC.clear()
        elif status == "Playing":
            start, end = get_timestamps(player)
            artist = player.get_artist()
            if len(artist) == 0:
                artist = "Studying.."
            RPC.update(
                details=player.get_title(),
                state=artist,
                large_image="pw",
                large_text=get_song(player),
                small_image='nil', # make a pull request
                start=start,
                end=end,
                buttons=[{"label": "Physics Wallah 🌐", "url": "https://discord.gg/physicswallah"}, {"label": "GitHub ✨", "url": "https://github.com/its-ag/"}],
            )
        elif status == "Paused":
            RPC.update(state='Paused', 
            # large_image='music', small_image='pause'
                large_image="pw",
                small_image='nil', # make a pull request
                buttons=[{"label": "Physics Wallah 🌐", "url": "https://discord.gg/physicswallah"}, {"label": "GitHub ✨", "url": "https://github.com/its-ag/"}],
            )
    except pypresence.exceptions.InvalidID:
        print("Lost connection to Discord RPC! Attempting reconnection...")
        connect_rpc()

def on_play(player, status, manager):
    update(player)

def on_pause(player, status, manager):
    update(player)

def on_metadata(player, metadata, manager):
    update(player)

def on_seeked(player, pos, manager):
    update(player)

def on_player_add(manager, name):
    setup_player(name)

def on_player_remove(manager, player):
    if len(manager.props.players) < 1:
        try:
            RPC.clear()
        except pypresence.exceptions.InvalidID:
            if e == "Client ID is Invalid":
                print("Lost connection to Discord RPC! Attempting reconnection...")
                connect_rpc()
            else:
                raise
    else:
        update(manager.props.players[0])

def start():
    manager.connect('name-appeared', on_player_add)
    manager.connect('player-vanished', on_player_remove)

    # Start program, connect to Discord, setup existing players & hook into GLib's main loop
    connect_rpc()

    for name in manager.props.player_names:
        setup_player(name)

    GLib.MainLoop().run()

if __name__ == '__main__':
    try:
        start()
    except KeyboardInterrupt:
        print("Shutting down...")
        RPC.clear()
        RPC.close()
