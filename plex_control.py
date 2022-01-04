import asyncio
import json
import re
import time
import traceback
from datetime import datetime
from difflib import SequenceMatcher
from threading import Thread
from typing import List

import redis
from pykodi import get_kodi_connection, Kodi
from colorama import init

init(convert=True)

r = redis.Redis(host='cloud.muddy.ca', port=6399, db=0, password="vWw@U4mzCw2am02iDFYp")

lock = False
EVERY = 0.1
UPDATE_INTERVAL = 600

sxex = re.compile("^(s\d+e\d+)$")


def similar(a, b, use_seq=False):
    if use_seq:
        return SequenceMatcher(None, a, b).ratio()
    score = 0
    b = b.lower()
    a = a.lower()
    for word in b.split():  # for every word in your string
        if word in a:  # if it is in your bigger string increase score
            score += 1
    # print(a, b, score)
    return score


def is_season_episode(command):
    return bool(sxex.match(command.lower()))


async def engage_lock():
    global lock
    if not lock:
        lock = True
        # print(f"{'-' * 5}locked{'-' * 5}")
        await asyncio.sleep(5)
        lock = False
        # print(f"{'-' * 5}unlocked{'-' * 5}")


class PlayerCluster:
    def __init__(self):
        self.update_library_counter = 0
        self.update_title_counter = 0
        self.players = {}
        self.latest_update_came_at = datetime.now()
        self.kodi_players: List[KodiControlledPlayer] = []

    async def run(self):
        await self.connect_target("localhost", "8080", "kodi", "0723"),
        # await self.connect_target("192.168.50.196", "8080", "kodi", "0723")
        await self.waiting_signals()

    async def connect_target(self, ip: str, port: str, username: str, password: str):
        kc = get_kodi_connection(ip, port, None, username, password)
        await kc.connect()
        kodi = Kodi(kc)
        await kodi.ping()
        properties = await kodi.get_application_properties(["name", "version"])
        print(properties)
        k_player = KodiControlledPlayer(kc, kodi)
        await k_player.update()
        self.kodi_players.append(k_player)
        print("Connected: " + ip)

    def print_title(self):
        s = ""
        for key, value in self.players.items():
            view_percentage = round(int(value['position']) / int(value['duration']) * 100, 1)
            s += f"[{key} {value['state']}:{value['title']} {view_percentage}%] "
        s += f"Last Update: {int((datetime.now() - self.latest_update_came_at).total_seconds())} seconds ago"
        print(f"\x1b]0;{s}\x07", end='')

    async def handler(self, message):
        data = message['data']
        if isinstance(data, int):
            return
        data = str(data.decode('utf-8'))
        args = data.split(" ")
        if len(args) == 0:
            return
        if args[0] == "status":
            status = json.loads(data.replace(f"{args[0]} ", ""))
            self.status_update(status)
            return
        print(args)
        for k in self.kodi_players:
            await k.handler(args, data)

    def status_update(self, status):
        self.players[status['identifier']] = status
        self.latest_update_came_at = datetime.now()
        self.print_title()

    async def waiting_signals(self):
        while True:
            if do_exit:
                for k in self.kodi_players:
                    await k.kc.close()
                return
            message = p.get_message()
            if message:
                await self.handler(message)
            time.sleep(EVERY)
            self.update_library_counter += EVERY
            self.update_title_counter += EVERY
            if self.update_library_counter > UPDATE_INTERVAL:
                self.update_library_counter = 0
                for k in self.kodi_players:
                    await k.update()
            if self.update_title_counter > 1:
                self.update_title_counter = 0
                self.print_title()


class KodiControlledPlayer:
    def __init__(self, kc, kodi):
        self.kodi = kodi
        self.kc = kc

    async def update(self):
        self.movies = await self.kodi.get_movies()
        self.tvshows = await self.kodi.get_tv_shows()
        # print(f"Fetched: {self.movies['limits']['total']} Movies & {self.tvshows['limits']['total']} Shows")

    def find_id(self, content, id_name, lf_title, append_print):
        print(f"Looking for: {lf_title}")
        sim = 0
        cid = 0
        title = ""
        results = {}
        for c in content:
            t_sim = similar(c['label'], lf_title)
            results[c[id_name]] = [t_sim, c['label']]
        results = dict(sorted(results.items(), key=lambda item: item[1][0], reverse=True))
        highest_sim = next(iter(results.values()))[0]
        if highest_sim == 0:
            print("Unable to find anything")
            return -1
        for key, value in results.items():
            if value[0] == highest_sim:
                t_sim = similar(value[1], lf_title, True)
                if t_sim > sim:
                    sim = t_sim
                    cid = int(key)
                    title = value[1]
            else:
                print(
                    f"Found, highest matching score: {title}, Id: {cid} , simple: {highest_sim} | seq: {sim} {append_print}")
                return cid

    async def handler(self, args, data):
        try:
            if args[0] == "play":  # play
                await self.kodi.play()
            if args[0] == "pause":
                await self.kodi.pause()
            elif args[0] == "seek":
                if len(args) == 2 and not lock:
                    await self.kodi.media_seek(int(args[1]))
            elif args[0] == "vol":
                if len(args) == 2:
                    await self.kodi.set_volume_level(int(args[1]))  # 0 - 100
            elif args[0] == "movie":
                if len(args) == 1:
                    return
                mid = self.find_id(self.movies["movies"], "movieid", data.replace(f"{args[0]} ", ""), "")
                if mid == -1:
                    return
                await self.kodi.play_item({"movieid": mid})
                await engage_lock()
                await self.kodi.media_seek(0)
            elif args[0] == "show" or is_season_episode(args[0]):
                if len(args) < 2:
                    return
                if is_season_episode(args[0]):
                    m = re.findall(r'\d+', args[0])
                    lf_season = m[0]
                    lf_episode = m[1]
                    lf_title = data.replace(f"{args[0]} ", "")
                else:
                    lf_season = args[1]
                    lf_episode = args[2]
                    lf_title = data.replace(f"{args[0]} {args[1]} {args[2]} ", "")
                tid = self.find_id(self.tvshows["tvshows"], "tvshowid", lf_title,
                                   f"| will navigate to season {lf_season} episode {lf_episode}")
                if tid == -1:
                    return
                episodes = await self.kodi.get_episodes(tid, int(lf_season))
                for episode in episodes['episodes']:
                    if str(lf_episode) in episode['label'][1:5]:
                        await self.kodi.play_item({"episodeid": int(episode['episodeid'])})
                        await engage_lock()
                        await self.kodi.media_seek(0)
                        return
        except Exception:
            print(traceback.format_exc())


def inputs():
    global do_exit
    while True:
        x = input("")
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
    s3e2 show_title / show season episode show_title
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

    manager = PlayerCluster()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(manager.run())
