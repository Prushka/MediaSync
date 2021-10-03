from plexapi.media import Session


class MediaPlayer():

    def get_media_title(self) -> str:
        pass

    def get_media_duration(self) -> float:
        pass

    def get_key(self) -> str:
        pass


class PlexPlayer(MediaPlayer):

    def __init__(self, session: Session):
        self.update(session)

    def update(self, session: Session):
        self.session_key = session.session_key
        self.title = session.grandparentTitle
        self.subtitle = session.title
        self.duration = session.duration
        self.session = session

    def update_state(self, state, position):
        self.state = state
        self.position = position
