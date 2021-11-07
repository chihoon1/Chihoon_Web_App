from copy import deepcopy
from operator import itemgetter
from itertools import product

# use the commented import for testing.py
'''
from gomoku_engine import *
'''
from .gomoku_engine import *

# direction is described as the opposite from (-1,-1) to (0,-1), but the other pairs are as what it should be
global direction_translator  # used to covert pair of indices to direction
direction_translator = {'-1-1': 'SE', '-10': 'down', '-11': 'SW', '0-1': 'right', \
                                '01': 'Oright', '1-1': 'OSE', '10': 'Odown', '11':'OSW'}
global actions  # action can be done by a player. represent (x,y) point on the board
actions = [(i, j) for i in range(15) for j in range(15)]

global direction_sign_translator
direction_sign_translator = {"right": (0, 1), "down": (1, 0), "SE": (1, 1), "SW": (1, -1)}


def del_subsequent_elem(lst: list, start_index: int, end_index: int):
    start = start_index if start_index < end_index else end_index
    end = end_index if end_index > start_index else start_index
    for i in range(start, end):
        lst.pop()  # better time complexity. Also, anyway elem between start and end will be gone


class Player():
    def __init__(self, name, color):
        self.player_name = name
        self.player_color = color

    def __str__(self):
        return str(self.player_name)


class AIPlayer(Player):
    def __init__(self, color, difficulty: str):
        super().__init__("Computer", color)
        self.ply = ['easy', 'medium', 'hard'].index(difficulty) + 1  # maximum play level to look ahead

    def alternate_static_value(self, state: Gomoku):
        # calculate static value of the current state on the Gomoku board
        # return the static value(float)
        skip_dict = {"right": [], "down": [], "SE": [], "SW": []}
        total_points = 0
        count = 0
        for i, j in product(range(15), range(15)):
            if count == state.turns: break
            if state.grid[i][j]["stone"] == None: continue
            for direct in ("right", "down", "SE", "SW"):
                r_sign, c_sign = direction_sign_translator[direct]
                if (i, j) in skip_dict[direct]:
                    skip_dict[direct].remove((i, j))
                    continue
                num_seq = state.grid[i][j][direct]  # number of sequence in a row in a particular direction
                in_range = True if (0 <= i - 1*r_sign < 15) and (0 <= j - 1*c_sign < 15) else False
                one_side_closed, other_side_closed = 0, 0
                opponent = abs(state.grid[i][j]["stone"] - 1)
                if not in_range or state.grid[i - 1*r_sign][j - 1*c_sign]["stone"] == opponent:
                    one_side_closed = 1/2
                in_range = True if (0 <= i + num_seq*r_sign < 15) and (0 <= j + num_seq*c_sign < 15) else False
                if not in_range or state.grid[i + num_seq*r_sign][j + num_seq*c_sign]["stone"] == opponent:
                    other_side_closed = 1/2
                row = num_seq
                exponent = row if row <= 5 else 0
                point_sign = 1 if state.grid[i][j]["stone"] == self.player_color else -1
                if exponent == 5: return point_sign * 900000000
                total_points += (1 - one_side_closed - other_side_closed) * point_sign * pow(10, exponent)
                if row > 1:
                    for k in range(1, row):
                        skip_dict[direct].append((i + k*r_sign, j + k*c_sign))
            count += 1
        return total_points

    def ABPruning(self, state: Gomoku, prev_move, alpha=-999999999, beta=999999999, curr_ply=0):
        # this is min-max search algorithm with Alpha Beta pruning to increase the efficiency in running time
        # prev_move is a pair where the first element is row index and the second is column index
        # return the tuple of best score of the optimal action and the corresponding next best move
        provision_v: float
        is_max = 1 if self.player_color == state.whose_turn else 0  # computer is max, and opponent is min
        if alpha >= beta:  # alpha beata pruning case
            if is_max: return alpha, None
            else: return beta, None
        if state.win(prev_move[0], prev_move[1]):
            return self.alternate_static_value(state), prev_move
        # create the successors of the current state with legal moves
        successor_lst = []
        row_dir, col_dir = [-1, 0, 1], [-1, 0, 1]
        scope_ext = state.turns // 15
        row_lst = [i*direction for direction in (-1, 1) for i in range(1, 5+scope_ext)]
        col_lst = [i*direction for direction in (-1, 1) for i in range(1, 5+scope_ext)]
        row_lst.append(0)
        col_lst.append(0)
        row_lst.sort()
        col_lst.sort()
        for r in range(-1*(2+scope_ext), (3+scope_ext)):
            for c in range(-1*(2+scope_ext), (3+scope_ext)):
                row, col = prev_move[0] + r, prev_move[1] + c
                if 0 <= row < 15 and 0 <= col < 15:
                    new_state = deepcopy(state)
                    if new_state.can_move(row, col, state.whose_turn)[0]:
                        new_state.move(row, col, state.whose_turn)
                        static_v = self.alternate_static_value(new_state) if curr_ply + 1 == self.ply else 0
                        successor_lst.append((static_v, new_state, (row, col)))
                    else:
                        del new_state
        # if current = max, then more efficient if successors sorted in descending
        # this may increase the chance of alpha-beta pruning on the parent leaf level
        if curr_ply+1 == self.ply:  # base case (successors are leaf nodes)
            successor_lst.sort(key=itemgetter(0), reverse=is_max)
            best_score, optimal_action = successor_lst[0][0], successor_lst[0][2]
            # print(f"leaf level: {curr_ply+1}, alpha: {alpha}, beta: {beta}, and provisional value: {best_score}")
            return best_score, optimal_action
        else:
            for elem in successor_lst:
                provision_v, action = self.ABPruning(elem[1], prev_move, alpha, beta, curr_ply+1)  # recursion to run in DFS search
                # print(f"I'm {is_max} max, and alpha: {alpha}, beta: {beta}, and provisional value: {provision_v}")
                if is_max and alpha < provision_v:
                    alpha, optimal_action = provision_v, elem[2]
                if not is_max and beta > provision_v:
                    beta, optimal_action = provision_v, elem[2]
        # print(f"current ply level: {curr_ply}")
        if is_max: return alpha, optimal_action
        else: return beta, optimal_action



if __name__ == '__main__':
    plyr = AIPlayer(0, "easy")
    state = gomoku_engine.Gomoku()

    old_state = deepcopy(state)
    state.move(3,4,1)
    #plyr.update_static_value(plyr.calculate_static_value(old_state, state, 3, 4))
    #v, act = plyr.ABPruning(state, (3, 4))
    #row, col = act
    #state.move(row, col, 0)
    state.move(4,8,0)
    #print(state)

    old_state = deepcopy(state)
    state.move(4,4,1)
    #plyr.update_static_value(plyr.calculate_static_value(old_state, state, 4, 4))
    #v, act = plyr.ABPruning(state, (4, 4))
    #row, col = act
    #state.move(row, col, 0)
    state.move(5,7,0)


    old_state = deepcopy(state)
    state.move(5,4,1)
    #plyr.update_static_value(plyr.calculate_static_value(old_state, state, 5, 4))
    #old_state.move(1,2,0)
    #print(plyr.alternate_static_value(old_state))
    #state.move(2,4,0)
    #print(plyr.alternate_static_value(state))  # higher
    v, act = plyr.ABPruning(state, (5, 4))
    row, col = act
    state.move(row, col, 0)
    #state.move(2,4,0)
    print(state)
    #print(plyr.alternate_static_value(state))  # worked
    old_state = deepcopy(state)
    state.move(1,4,1)
    plyr.update_static_value(plyr.calculate_static_value(old_state, state, 1, 4))
    v, act = plyr.ABPruning(state, (4, 4))
    row, col = act
    state.move(row, col, 0)

