import asyncio
import json
import re
import traceback
from difflib import SequenceMatcher
from threading import Thread

import redis
from pykodi import get_kodi_connection, Kodi

r = redis.Redis(host='cloud.muddy.ca', port=6399, db=0, password="vWw@U4mzCw2am02iDFYp")
kc = get_kodi_connection("localhost", "8080", None, "kodi", "0723")
kodi: Kodi or None = None


def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()


def get_args(s):
    print(s)
    return re.findall('\[(.+?)]', s)


async def handler(message, movies, tvshows):
    sim = 0
    id = 0
    title = ""

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
            movie_args = get_args(data)
            if len(movie_args) == 0:
                return
            print(f"Looking for: {movie_args[0]}")
            for movie in movies["movies"]:
                t_sim = similar(movie['label'], movie_args[0])
                if t_sim > sim:
                    sim = t_sim
                    id = int(movie['movieid'])
                    title = movie['label']
            print(f"Found movie with highest matching score: {title}, {sim}")
            await kodi.play_item({"movieid": id})
        elif args[0] == "show":
            show_args = get_args(data)
            if len(show_args) < 3:
                return
            for show in tvshows["tvshows"]:
                t_sim = similar(show['label'], show_args[0])
                if t_sim > sim:
                    sim = t_sim
                    id = int(show['tvshowid'])
                    title = show['label']
            print(
                f"Found tvshow with highest matching score: {title}, {sim}, will navigate to season {show_args[1]} episode {show_args[2]}")
            episodes = await kodi.get_episodes(id, int(show_args[1]))
            for episode in episodes['episodes']:
                if str(int(show_args[2])) in episode['label'][1:5]:
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


def thread_a():
    while True:
        x = input()
        if x.lower() == "exit":
            break
        r.publish("saine", x)
        # print(f"Published: {x}")


if __name__ == '__main__':
    p = r.pubsub()
    p.subscribe("saine")

    thread_a = Thread(target=thread_a, daemon=True)
    thread_a.start()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(connect())
