# settings.py
import asyncio
from typing import Dict

from pyatv import interface

from MediaPlayer import PlexPlayer, ATVPlayer

plexPlayers: Dict[str, PlexPlayer]
atv: ATVPlayer or None
atv = None
loop = asyncio.get_event_loop()
lock = False

leading_player = ["kodi", "Prushka"]
synced_players = [["kodi", "Prushka"], ["kodi", "saine_"]]


def init():
    global plexPlayers
    plexPlayers = {}


def find_player_by_session_key(session_key):
    for p in plexPlayers.values():
        if p.session_key == session_key:
            return p
    return None


async def engage_lock():
    global lock
    if not lock:
        lock = True
        print("===locked===")
        await asyncio.sleep(5)
        lock = False
        print("===unlocked===")


def has_initialized():
    return atv is not None
