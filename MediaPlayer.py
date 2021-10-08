import json
import time
from abc import abstractmethod
from enum import Enum
from pprint import pprint
from typing import List

from plexapi.client import PlexClient
from plexapi.media import Session, Media
from plexapi.server import PlexServer
from pyatv import interface, const
from pyatv.interface import Playing

import redis_populate
import settings


class PlayerState(Enum):
    PLAYING = 0
    PAUSED = 1
    UNKNOWN = 2

    @classmethod
    def is_valid(cls):
        return cls.value == 0 or cls.value == 1


class MediaPlayer:
    @abstractmethod
    def get_media_title(self) -> str:
        pass

    @abstractmethod
    def get_media_duration(self) -> float:
        pass

    @abstractmethod
    def get_media_position(self) -> float:
        pass

    @abstractmethod
    def get_state(self) -> PlayerState:
        pass

    @abstractmethod
    def get_identifier(self) -> str:
        pass

    def before_update(self):
        print(f"[{self.get_identifier()}] [{self.get_media_title()}: {self.get_state()} - {self.get_media_position()}]",
              end='')

    def after_update(self):
        print(f" -> [{self.get_media_title()}: {self.get_state()} - {self.get_media_position()}]")
        # redis_populate.r.set(self.get_identifier(), json.dumps(self.get_media_json()))

    @abstractmethod
    def ab_update(self, *args):
        pass

    def update(self, *args):
        self.before_update()
        self.ab_update(*args)
        self.after_update()

    def is_playing(self):
        return self.get_state() == PlayerState.PLAYING

    def is_paused(self):
        return self.get_state() == PlayerState.PAUSED

    def get_media_json(self):
        return {"title": self.get_media_title(), "position": self.get_media_position(),
                "state": self.get_state().value, "duration": self.get_media_duration()}


class ControllableMediaPlayer:
    @abstractmethod
    def pause(self):
        pass

    @abstractmethod
    def resume(self):
        pass

    @abstractmethod
    def seek(self, position: int):  # position: seconds
        pass

    @abstractmethod
    def play_media(self, media, offset):
        pass

    @abstractmethod
    def sync_with(self, player: MediaPlayer):
        pass


class PlexPlayer(MediaPlayer, ControllableMediaPlayer):

    def __init__(self, session: Session, server: PlexServer):
        self.server = server
        self.set_session(session)

    def ab_update(self, state, position, rating_key):
        if state == "playing":
            self.state = PlayerState.PLAYING
        elif state == "paused":
            self.state = PlayerState.PAUSED
        else:
            self.state = PlayerState.UNKNOWN
        self.position = position / 1000
        self.rating_key = rating_key

    def set_session(self, session):
        self.session_key = session.sessionKey
        self.title = session.title
        self.duration = session.duration
        self.session: Session = session
        self.product = session.players[0].product
        self.platform = session.players[0].platform
        self.username = session.usernames[0]
        self.client: PlexClient = session.players[0]
        self.client.proxyThroughServer()
        # pprint(vars(session))
        self.state = PlayerState.UNKNOWN
        self.position = 0
        self.rating_key = -1
        if self.is_kodi():
            self.update(self.client.state, session.viewOffset, session.ratingKey)

    def compare_rating_key(self, rating_key):
        return rating_key == self.rating_key

    def is_kodi(self):
        return "kodi" in self.get_identifier()

    def is_infuse_tvos(self):
        return self.product == "Infuse" and self.platform == "tvOS"

    def get_media_title(self) -> str:
        return self.title

    def get_media_duration(self) -> float:
        return self.duration

    def get_media_position(self) -> float:
        return self.position

    def get_key(self) -> str:
        return self.session_key

    def get_state(self) -> PlayerState:
        return self.state

    def get_identifier(self) -> str:
        return f"{self.product} {self.platform} {self.username}".lower()

    def get_media(self):
        return self.session

    def pause(self):
        # self.client.pause()
        redis_populate.r.publish("saine", "pause")

    def resume(self):
        redis_populate.r.publish("saine", "play")

    def seek(self, position: int):
        redis_populate.r.publish("saine", f"seek {position}")

    def play_media(self, media: Media, offset):
        self.client.playMedia(media, offset)

    def refresh(self):
        for session in self.server.sessions():
            if session.sessionKey == self.session_key:
                self.set_session(session)
                return

    def sync_with(self, player: MediaPlayer):
        # if player.keywords_match(settings.leading_player) and self.get_media_title() != player.get_media_title():
        #     print(self.get_media_title(), player.get_media_title())
        #     self.play_media(player.get_media(), offset=player.get_media_position())
        #     del settings.plexPlayers[self.get_identifier()]
        # else:
        if self.get_identifier() == player.get_identifier():
            return

        self.refresh()
        print(f"{self.get_identifier()} SYNCING WITH {player.get_identifier()}")
        if abs(player.get_media_position() - self.get_media_position()) > 6:
            self.seek(int(player.get_media_position()))
        if self.is_playing() and player.is_paused():
            self.pause()
        elif self.is_paused() and player.is_playing():
            self.resume()


class ATVPlayer(MediaPlayer, ControllableMediaPlayer):
    def __init__(self, atv: interface.AppleTV, init_state: Playing):
        self.atv = atv
        self.playing: Playing = init_state

    def get_identifier(self) -> str:
        return "ATVPlayer"

    def playstatus_update(self, updater, playstatus: Playing) -> None:
        """Inform about changes to what is currently playing."""
        # print(30 * "-" + "\n", playstatus)
        self.before_update()
        self.playing = playstatus
        self.after_update()

    def playstatus_error(self, updater, exception: Exception) -> None:
        """Inform about an error when updating play status."""
        print("Error:", exception)

    def get_media_title(self) -> str:
        return self.playing.title

    def get_media_duration(self) -> float:
        return self.playing.total_time

    def get_key(self) -> str:
        return "0"

    def get_media_position(self) -> float:
        return self.playing.position

    def get_state(self) -> PlayerState:
        if self.playing.device_state == const.DeviceState.Playing:
            return PlayerState.PLAYING
        elif self.playing.device_state == const.DeviceState.Paused:
            return PlayerState.PAUSED
        else:
            return PlayerState.UNKNOWN

    def pause(self):
        settings.loop.run_until_complete(self.atv.remote_control.pause())

    def resume(self):
        settings.loop.run_until_complete(self.atv.remote_control.play())

    def seek(self, position: float):
        settings.loop.run_until_complete(self.atv.remote_control.skip_forward())
