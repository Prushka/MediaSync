import asyncio
import time
from pprint import pprint
from typing import List, Dict

import plexapi
from plexapi.alert import AlertListener
from plexapi.client import PlexClient
from plexapi.media import Session
from plexapi.myplex import MyPlexAccount, MyPlexResource
from plexapi.server import PlexServer, SystemAccount
from plexapi.video import Movie
from plexwebsocket import PlexWebsocket, SIGNAL_CONNECTION_STATE, STATE_CONNECTED, STATE_DISCONNECTED, STATE_STOPPED

baseurl = 'http://marnie:32400'
token = 'Cn55vSNPf-BDLyz7JQ3-'
plex_server = PlexServer(baseurl, token)

plex_account = plexapi.myplex.MyPlexAccount(token="Cn55vSNPf-BDLyz7JQ3-")

sessions: Dict[int, Session] = {}


def fetch_new_sessions():
    sessions.clear()
    for session in plex_server.sessions():
        # pprint(vars((session)))
        # print(session.viewOffset)
        # print(session.usernames)
        if "saine_" in session.usernames:
            sessions[session.sessionKey] = session
    print(sessions)


def find_rating_key(rating_key):
    for sessionkey, session in sessions.items():
        if rating_key == session.ratingKey:
            return True
    return False


def update_session(payload):
    session_payload = payload["PlaySessionStateNotification"][0]

    state = session_payload["state"]
    session_key = int(session_payload["sessionKey"])
    offset = int(session_payload["viewOffset"])
    rating_key = int(session_payload["ratingKey"])

    if session_key not in sessions:
        fetch_new_sessions()
        if session_key not in sessions:
            print(f"cannot find session: {session_key}")
            return

    if not find_rating_key(rating_key):
        fetch_new_sessions()
    if not find_rating_key(rating_key):
        print(f"cannot find session with rating key, websocket: {session_key}, rating: {rating_key}")


def print_info(msgtype, data, error):
    """Handle callbacks from plexwebsocket library."""
    if msgtype == SIGNAL_CONNECTION_STATE:

        if data == STATE_CONNECTED:
            print("plex connected")
            fetch_new_sessions()
        elif data == STATE_DISCONNECTED:
            print("websocket disconnected")
        # Stopped websockets without errors are expected during shutdown and ignored
        elif data == STATE_STOPPED and error:
            print("websocket stopped")

    elif msgtype == "playing":
        # print(f"Playing Data: {data}")
        update_session(data)
    elif msgtype == "status":
        print(f"Status Data: {data}")
    #else:
        #print(data)


async def main():
    ws = PlexWebsocket(plex_server, print_info, subscriptions=[])
    await ws.listen()


async def callback(data):
    print(data)


if __name__ == '__main__':
    # account = MyPlexAccount('szcezliwy@hotmail.com', 'NeQC[N4%Myd6-kc*')
    # saine = account.resource('marnie').connect()  # returns a PlexServer instance

    # for client in plex_account.resources():
    #     pprint(vars(client))
    # print("Session")

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

    # print("Clients")
    # for client in plex_server.sessions():
    #    pprint(vars(client))
