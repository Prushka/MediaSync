import asyncio

from plexapi.media import Session
from plexapi.server import PlexServer
from plexwebsocket import PlexWebsocket, SIGNAL_CONNECTION_STATE, STATE_CONNECTED, STATE_DISCONNECTED, STATE_STOPPED

import redis_populate
import settings
from MediaPlayer import PlexPlayer

baseurl = 'http://marnie:32400'
token = 'Cn55vSNPf-BDLyz7JQ3-'
plex_server = PlexServer(baseurl, token)


# plex_account = plexapi.myplex.MyPlexAccount(token="Cn55vSNPf-BDLyz7JQ3-")

def fetch_new_sessions():
    session: Session
    settings.plexPlayers.clear()
    for session in plex_server.sessions():
        pp = PlexPlayer(session, plex_server)
        if pp.is_kodi():
            settings.plexPlayers[pp.get_identifier()] = pp
    print(f"Fetched new sessions: {list(settings.plexPlayers.keys())}")


def update_session(payload):
    session_payload = payload["PlaySessionStateNotification"][0]
    state = session_payload["state"]
    session_key = int(session_payload["sessionKey"])
    offset = int(session_payload["viewOffset"])
    rating_key = int(session_payload["ratingKey"])

    player = settings.find_player_by_session_key(session_key)
    if player is None:
        fetch_new_sessions()
        player = settings.find_player_by_session_key(session_key)
    if player is None:
        return

    player.update(state, offset, rating_key)

    # if not player.compare_rating_key(rating_key):
    #     fetch_new_sessions()
    # if not player.compare_rating_key(rating_key):
    #     print(f"cannot find session with rating key, websocket: {session_key}, rating: {rating_key}")

    # if not (player.is_infuse_tvos() or not settings.has_initialized()):
    #     if player.is_valid_state():
    #         if settings.atv.is_playing() and player.is_paused():
    #             settings.atv.pause()
    #         elif settings.atv.is_paused() and player.is_playing():
    #             settings.atv.resume()

    #     if player.get_media_position() is None or settings.atv.get_media_position() is None:
    #         return
    #     if abs(player.get_media_position() - settings.atv.get_media_position()) > 15:
    #         # seek atv to match
    #         settings.atv.seek(player.get_media_position())
    for p in settings.plexPlayers.values():
        try:
            p.sync_with(player)
        except Exception as e:
            print(e)
    return


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
    # else:
    # print(data)


async def poll():
    while True:
        print("Polling...")
        fetch_new_sessions()
        await asyncio.sleep(2)


async def main():
    ws = PlexWebsocket(plex_server, print_info, subscriptions=["playing", "status"])
    input_coroutines = [ws.listen()]
    await asyncio.gather(*input_coroutines, return_exceptions=True)


if __name__ == '__main__':
    # account = MyPlexAccount('szcezliwy@hotmail.com', 'NeQC[N4%Myd6-kc*')
    # saine = account.resource('marnie').connect()  # returns a PlexServer instance
    print("hello world")
    # redis_populate.flush()
    # settings.init()
    # settings.loop.run_until_complete(main())
