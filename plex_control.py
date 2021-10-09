import asyncio
import re
import time
import traceback
from difflib import SequenceMatcher
from threading import Thread

import redis
from pykodi import get_kodi_connection, Kodi

r = redis.Redis(host='cloud.muddy.ca', port=6399, db=0, password="vWw@U4mzCw2am02iDFYp")

kodi: Kodi or None = None
lock = False


async def engage_lock():
    global lock
    if not lock:
        lock = True
        print(f"{'-' * 5}locked{'-' * 5}")
        await asyncio.sleep(5)
        lock = False
        print(f"{'-' * 5}unlocked{'-' * 5}")


def similar(a, b):
    # return SequenceMatcher(None, a, b).ratio()
    score = 0
    b = b.lower()
    a = a.lower()
    for word in b.split():  # for every word in your string
        if word in a:  # if it is in your bigger string increase score
            score += 1
    print(a, b, score)
    return score


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
            if len(args) == 2 and not lock:
                await kodi.media_seek(int(args[1]))
        elif args[0] == "movie":
            g_title = data.replace(f"{args[0]} ", "")
            print(f"Looking for: {g_title}")
            for movie in movies["movies"]:
                t_sim = similar(movie['label'], g_title)
                if t_sim > sim:
                    sim = t_sim
                    id = int(movie['movieid'])
                    title = movie['label']
            print(f"Found movie with highest matching score: {title}, {sim}")
            await kodi.play_item({"movieid": id})
            await engage_lock()
            await kodi.media_seek(0)
        elif args[0] == "show":
            if len(args) < 3:
                return
            g_title = data.replace(f"{args[0]} {args[1]} {args[2]} ", "")
            for show in tvshows["tvshows"]:
                t_sim = similar(show['label'], g_title)
                if t_sim > sim:
                    sim = t_sim
                    id = int(show['tvshowid'])
                    title = show['label']
            print(
                f"Found tvshow with highest matching score: {title}, {sim}, will navigate to season {args[1]} episode {args[2]}")
            episodes = await kodi.get_episodes(id, int(args[1]))
            for episode in episodes['episodes']:
                if str(args[2]) in episode['label'][1:5]:
                    await kodi.play_item({"episodeid": int(episode['episodeid'])})
                    await engage_lock()
                    await kodi.media_seek(0)
                    break

    except Exception:
        print(traceback.format_exc())


async def connect():
    global kodi
    kc = get_kodi_connection("localhost", "8080", None, "kodi", "0723")
    await kc.connect()

    kodi = Kodi(kc)
    await kodi.ping()
    properties = await kodi.get_application_properties(["name", "version"])
    print(properties)

    movies = await kodi.get_movies()
    tvshows = await kodi.get_tv_shows()

    while True:
        if do_exit:
            await kc.close()
            return
        message = p.get_message()
        if message:
            await handler(message, movies, tvshows)
        time.sleep(0.01)  # be nice to the system :)


def inputs():
    global do_exit
    while True:
        x = input()
        if x.lower() == "exit":
            do_exit = True
            return
        # print(f"Published: {x}")
        r.publish("saine", x)


def print_help():
    print("""Commands:
    play
    pause
    seek seconds
    movie movie_title
    show season episode show_title
    exit
    Note:
    PLEASE EXIT USING exit command
    """)


do_exit = False

if __name__ == '__main__':
    print_help()
    p = r.pubsub()
    p.subscribe("saine")

    thread_a = Thread(target=inputs, daemon=False)
    thread_a.start()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(connect())
