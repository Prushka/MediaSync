import asyncio
import json
import traceback

import redis
from pykodi import get_kodi_connection, Kodi

r = redis.Redis(host='cloud.muddy.ca', port=6399, db=0, password="vWw@U4mzCw2am02iDFYp")
kc = get_kodi_connection("localhost", "8080", None, "kodi", "0723")
kodi: Kodi or None = None


async def handler(message, movies, tvshows):
    data = message['data']
    if isinstance(data, int):
        return
    data = str(data.decode('utf-8'))
    args = data.split(" ")
    print(args)
    try:
        if len(args) == 0:
            return
        if args[0] == "play":  # play
            await kodi.play()
        if args[0] == "pause":
            await kodi.pause()
        elif args[0] == "seek":
            if len(args) == 2:
                await kodi.media_seek(int(args[1]))
        elif args[0] == "movie":
            j = json.loads(data[5:])
            print(j)
            for movie in movies["movies"]:
                if movie['label'] == j['title']:
                    await kodi.play_item({"movieid": int(movie['movieid'])})
                    break
        elif args[0] == "show":
            j = json.loads(data[5:])
            print(j)
            for show in tvshows["tvshows"]:
                if show['label'] == j['title']:
                    episodes = await kodi.get_episodes(show['tvshowid'], j['season'])
                    for episode in episodes['episodes']:
                        if str(j['episode']) in episode['label'][2:5]:
                            await kodi.play_item({"episodeid": int(episode['episodeid'])})
                    break

    except Exception:
        print(traceback.format_exc())


async def connect():
    global kodi
    await kc.connect()

    kodi = Kodi(kc)
    await kodi.ping()
    properties = await kodi.get_application_properties(["name", "version"])
    print(properties)

    movies = await kodi.get_movies()
    tvshows = await kodi.get_tv_shows()

    for message in p.listen():
        await handler(message, movies, tvshows)


if __name__ == '__main__':
    p = r.pubsub()
    p.subscribe("saine")

    loop = asyncio.get_event_loop()
    loop.run_until_complete(connect())
    # thread = p.run_in_thread(sleep_time=0.001, daemon=False)

    # pprint(vars(client._session))
