import asyncio
import re
import sys
import threading
import time
import traceback
from threading import Thread

import redis
from pykodi import get_kodi_connection, Kodi
from colorama import init, Fore

r = redis.Redis(host='cloud.muddy.ca', port=6399, db=0, password="vWw@U4mzCw2am02iDFYp")

lock = False
EVERY = 0.1
init(convert=True)
previous_print = ""


def eprint(text):
    global previous_print
    # print(*args, file=sys.stderr, **kwargs)
    print('\e[A\e[kOutput\nCurrent state of the prompt', end='')
    previous_print = str(text)


def similar(a, b):
    # return SequenceMatcher(None, a, b).ratio()
    score = 0
    b = b.lower()
    a = a.lower()
    for word in b.split():  # for every word in your string
        if word in a:  # if it is in your bigger string increase score
            score += 1
    # print(a, b, score)
    return score


async def engage_lock():
    global lock
    if not lock:
        lock = True
        # print(f"{'-' * 5}locked{'-' * 5}")
        await asyncio.sleep(5)
        lock = False
        # print(f"{'-' * 5}unlocked{'-' * 5}")


def get_args(s):
    print(s)
    return re.findall('\[(.+?)]', s)


class KodiControlledPlayer:
    def __init__(self):
        self.kc = get_kodi_connection("localhost", "8080", None, "kodi", "0723")
        self.counter = 0

    async def update(self):
        self.movies = await self.kodi.get_movies()
        self.tvshows = await self.kodi.get_tv_shows()
        eprint(f"Fetched: {self.movies['limits']['total']} Movies & {self.tvshows['limits']['total']} Shows")

    async def connect(self):
        await self.kc.connect()
        self.kodi = Kodi(self.kc)
        await self.kodi.ping()
        properties = await self.kodi.get_application_properties(["name", "version"])
        eprint(properties)
        await self.update()

    async def waiting_signals(self):
        while True:
            if do_exit:
                await self.kc.close()
                return
            message = p.get_message()
            if message:
                await self.handler(message)
            time.sleep(EVERY)
            self.counter += EVERY
            if self.counter > 10:
                self.counter = 0
                await self.update()

    async def handler(self, message):
        sim = 0
        id = 0
        title = ""

        data = message['data']
        if isinstance(data, int):
            return
        data = str(data.decode('utf-8'))
        args = data.split(" ")
        eprint(args)
        try:
            if len(args) == 0:
                return
            if args[0] == "play":  # play
                await self.kodi.play()
            if args[0] == "pause":
                await self.kodi.pause()
            elif args[0] == "seek":
                if len(args) == 2 and not lock:
                    await self.kodi.media_seek(int(args[1]))
            elif args[0] == "movie":
                g_title = data.replace(f"{args[0]} ", "")
                eprint(f"Looking for: {g_title}")
                for movie in self.movies["movies"]:
                    t_sim = similar(movie['label'], g_title)
                    if t_sim > sim:
                        sim = t_sim
                        id = int(movie['movieid'])
                        title = movie['label']
                eprint(f"Found movie with highest matching score: {title}, {sim}")
                await self.kodi.play_item({"movieid": id})
                await engage_lock()
                await self.kodi.media_seek(0)
            elif args[0] == "show":
                if len(args) < 3:
                    return
                g_title = data.replace(f"{args[0]} {args[1]} {args[2]} ", "")
                for show in self.tvshows["tvshows"]:
                    t_sim = similar(show['label'], g_title)
                    if t_sim > sim:
                        sim = t_sim
                        id = int(show['tvshowid'])
                        title = show['label']
                eprint(
                    f"Found tvshow with highest matching score: {title}, {sim}, will navigate to season {args[1]} episode {args[2]}")
                episodes = await self.kodi.get_episodes(id, int(args[1]))
                for episode in episodes['episodes']:
                    if str(args[2]) in episode['label'][1:5]:
                        await self.kodi.play_item({"episodeid": int(episode['episodeid'])})
                        await engage_lock()
                        await self.kodi.media_seek(0)
                        break

        except Exception:
            eprint(traceback.format_exc())


def inputs():
    global do_exit
    while True:
        x = input(">")
        if x.lower() == "exit":
            do_exit = True
            return
        # print(f"Published: {x}")
        r.publish("saine", x)


def print_help():
    eprint("""Commands:
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

    k_player = KodiControlledPlayer()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(k_player.connect())
    loop.run_until_complete(k_player.waiting_signals())
