import os
from bisect import insort_left
from typing import List

from games.adapters.datareader.csvdatareader import GameFileCSVReader
from games.adapters.repository import AbstractRepository
from games.domainmodel.model import Game


class MemoryRepository(AbstractRepository):
    def __init__(self):
        self.__games = list()
        self.__tags = list()

    def add_game(self, game: Game):
        if isinstance(game, Game):
            # When inserting the game, keep the game list sorted alphabetically by the id.
            # Games will be sorted by game due to __lt__ method of the Game class.
            insort_left(self.__games, game)

    def get_games(self) -> List[Game]:
        return self.__games

    def get_game(self, id: int) -> Game:
        for g in self.__games:
            if g.game_id == id: return g
        return None

    def get_number_of_games(self):
        return len(self.__games)
    
    def get_tags(self) -> list[str]:
        return self.__tags

    def add_tag(self, tag: str):
        if tag not in self.__tags:
            self.__tags.append(tag)


def populate(repo: AbstractRepository):
    dir_name = os.path.dirname(os.path.abspath(__file__))
    games_file_name = os.path.join(dir_name, "data/games.csv")
    reader = GameFileCSVReader(games_file_name)

    reader.read_csv_file()

    games = reader.dataset_of_games
    tags = reader.dataset_of_tags

    # Add games to the repo:
    for game in games:
        repo.add_game(game)
    
    # Add tags to the repo:
    for tag in tags:
        repo.add_tag(tag)
