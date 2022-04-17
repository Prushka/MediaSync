import asyncio
import json

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
    await play_tvshow(kodi, 102, 1, 9)
    await kc.close()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
