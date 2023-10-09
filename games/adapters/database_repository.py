from pathlib import Path
from typing import List

from sqlalchemy.orm import scoped_session
from sqlalchemy.orm.exc import NoResultFound

from games.adapters.datareader.csvdatareader import GameFileCSVReader
from games.adapters.repository import AbstractRepository
from games.domainmodel.model import Publisher, Game, Genre, Review, User, Tag


# This manages the session to the database and lets us very simply interface with SQLAlchemy
class SessionContextManager:
    def __init__(self, session_factory):
        self.__session_factory = session_factory
        self.__session = scoped_session(self.__session_factory)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.rollback()

    @property
    def session(self):
        return self.__session

    def commit(self):
        self.__session.commit()

    def rollback(self):
        self.__session.rollback()

    def reset_session(self):
        # this method can be used e.g. to allow Flask to start a new session for each http request,
        # via the 'before_request' callback
        self.close_current_session()
        self.__session = scoped_session(self.__session_factory)

    def close_current_session(self):
        if not self.__session is None:
            self.__session.close()


class DatabaseRepository(AbstractRepository):
    def __init__(self, session_factory):
        self.__scm = SessionContextManager(session_factory)

    def close_session(self):
        self.__scm.close_current_session()

    def reset_session(self):
        self.__scm.reset_session()

    def add_publisher(self, publisher: Publisher):
        with self.__scm as scm:
            scm.session.merge(publisher)
            scm.commit()

    def add_game(self, game: Game):
        with self.__scm as scm:
            scm.session.merge(game)
            scm.commit()

    def add_games(self, games: List[Game]):
        with self.__scm as scm:
            for game in games:
                scm.session.merge(game)
            scm.commit()

    def get_games(self) -> List[Game]:
        """ Returns the list of games. """
        return self.__scm.session.query(Game).all()

    def get_game(self, id: int) -> Game:
        """ Returns the game with the given id from the repository. """
        game = None
        with self.__scm as scm:
            try:
                game = scm.session.query(Game).filter(Game._Game__game_id == id).first()
            except NoResultFound:
                pass
        return game

    def get_number_of_games(self):
        """ Returns the number of games that exist in the repository. """
        with self.__scm as scm:
            return scm.session.query(Game).count()

    def add_genre(self, genre: Genre):
        with self.__scm as scm:
            scm.session.merge(genre)
            scm.commit()

    def add_genres(self, genres: List[Genre]):
        with self.__scm as scm:
            for genre in genres:
                scm.session.merge(genre)
            scm.commit()

    def get_genres(self) -> list[Genre]:
        with self.__scm as scm:
            return scm.session.query(Genre).all()

    def get_tags(self) -> list[Tag]:
        """ Returns the list of tags. """
        with self.__scm as scm:
            return scm.session.query(Tag).all()

    def search_games(self,
                     title: str = '',
                     price: float = float('inf'),
                     # release_date: (int, str idk),
                     tags: list[str] = None,
                     recommendations: int = 0,
                     genre: Genre = None ) -> list[Game]:
        """ Returns the list of games that match the given criteria. """
        games = []
        with self.__scm as scm:
            games = scm.session.query(Game)
            if title:
                games = games.filter(Game._Game__game_title.contains(title))
            games = games.filter(Game._Game__price <= price, Game._Game__recommendations >= recommendations)
            
            games = games.all()

            # If someone know how to do this with SQLAlchemy, please let me know
            if genre:
                if isinstance(genre, str):
                    genre = Genre(genre)
                filtered_games = []
                for game in games:
                    if genre in game.genres:
                        filtered_games.append(game)
                games = filtered_games

            if tags:
                filtered_games = []
                tags = [Tag(t) for t in tags]
                for game in games:
                    if all(tag in game.tags for tag in tags):
                        filtered_games.append(game)
                games = filtered_games
                

        return games
    
    def get_user(self, username: str):
        """ Gets a user from the repository. """
        user = None
        try:
            user = self.__scm.session.query(User).filter(User._User__username == username).one()
        except NoResultFound:
            # Ignore any exception and return None.
            pass

        return user

    def add_user(self, user):
        """ Adds a user to the repository. """
        with self.__scm as scm:
            scm.session.add(user)
            scm.commit()

    def add_review(self, review):
        """ Adds a review to the repository. """
        if isinstance(review, Review):
            with self.__scm as scm:
                scm.session.add(review)
                scm.commit()



def populate(data_path: Path, repo: AbstractRepository):
    games_file_name = str(Path(data_path) / "games.csv")
    reader = GameFileCSVReader(games_file_name)

    reader.read_csv_file()

    publishers = reader.dataset_of_publishers
    games = reader.dataset_of_games
    tags = reader.dataset_of_tags
    genres = reader.dataset_of_genres

    # Add publishers to the repo:
    for publisher in publishers:
        repo.add_publisher(publisher)

    # Add games to the repo:
    repo.add_games(games)
    
    # Addding these specifically isn't needed because the ORM already automatically adds them when adding games & relates everything
    # for tag in tags:
    #     repo.add_tag(tag)
    # Add genres to the repo
    # repo.add_genres(genres)
