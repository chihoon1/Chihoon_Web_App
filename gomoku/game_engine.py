
class GameEngine:
    def __init__(self, game_type: str):
        if game_type == 'Board':
            self.whose_turn = 1

    def __str__(self):
        raise NotImplementedError

    def can_move(self):
        raise NotImplementedError

    def move(self):
        raise NotImplementedError

    def win(self):
        raise NotImplementedError
