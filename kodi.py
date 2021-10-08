import asyncio
import json

from jsonrpc_websocket import Server
from pykodi import get_kodi_connection, Kodi
import redis_populate

kc = get_kodi_connection("localhost", "8080", None, "kodi", "0723")


# if ws_port is None the connection will be over HTTP, otherwise over WebSocket.
# ssl defaults to False (only relevant if you have a proxy), timeout to 5 (seconds)
# session is generated if not passed in

async def play_movie(kodi: Kodi, movieid):
    movie = await kodi.get_movie_details(movieid)
    movie = movie["moviedetails"]
    redis_populate.r.publish("saine", "movie " + json.dumps({"title": movie['label']}))


async def play_tvshow(kodi: Kodi, tvshowid, season, episode):
    tvshow = await kodi.get_tv_show_details(tvshowid)
    tvshow = tvshow["tvshowdetails"]
    redis_populate.r.publish("saine", "show " + json.dumps({"title": tvshow['label'],
                                                            "season": season,
                                                            "episode": episode}))


async def main():
    await kc.connect()
    kodi = Kodi(kc)

    await kodi.ping()
    properties = await kodi.get_application_properties(["name", "version"])

    movies = await kodi.get_movies()
    tvshows = await kodi.get_tv_shows()
    for movie in movies['movies']:
        print(movie)
    print("=" * 10)
    for tvshow in tvshows['tvshows']:
        print(tvshow)
        # for i in range(0, 10):
        #     episodes = await kodi.get_episodes(tvshow['tvshowid'], i)
        #     if episodes['limits']['total'] == 0:
        #         break
        #     for episode in episodes['episodes']:
        #         print(episode)
    # print(await kodi.get_episodes(6, 1))
    # await kodi.play_item({"movieid":2})
    # await kodi.play_item({"episodeid": 112})
    # await play_movie(kodi, 150)
    await play_tvshow(kodi, 102, 1, 9)
    await kc.close()
    # await kodi.volume_up()
    # await kodi.pause()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
