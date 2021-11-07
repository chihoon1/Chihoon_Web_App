from copy import deepcopy

# use the commented import for testing.py
'''
from game_engine import GameEngine
'''
from .game_engine import GameEngine

# direction is described as the opposite from (-1,-1) to (0,-1), but the other pairs are as what it should be
global direction_translator  # used to covert pair of indices to direction
direction_translator = {'-1-1': 'SE', '-10': 'down', '-11': 'SW', '0-1': 'right', \
                                '01': 'Oright', '1-1': 'OSE', '10': 'Odown', '11':'OSW'}


class Gomoku(GameEngine):
    def __init__(self, turns=0, player1=0, player2=1):
        super().__init__('Board')
        self.winner = None

        # dict with an inner list
        # elements of the inner list = the # of successive stone in each direction and stone color in a (x, y) position
        self.grid = []
        for row_ind in range(15):
            self.grid.append([])
            for column_ind in range(15):
                self.grid[row_ind].append({'right': 0, 'down': 0, 'SE': 0, 'SW': 0, 'stone': None})

        self.turns = turns  # number of turns taken so far
        # Normally, player 1 will be designated to the user and player 2 to the computer player
        self.player1 = player1  # 0 white, and 1 black
        self.player2 = player2

    def __str__(self):
        str_version = ""
        for i in range(15):
            for j in range(15):
                stone_color = self.grid[i][j]["stone"]
                str_version += str(stone_color) + ' '
                if stone_color is not None: str_version += '   '
            str_version += "\n"
        return str_version

    def update_grid(self, row_index, col_index, plyr_color):
        '''
        count the # of successive same stone in the directions of Right, Down, SE, and SW
        Other directions are redundant
        one stone is sufficient to check for win, so other neighboring stones no need for update
        Invoked everytime can_move or move method are called
        :return: the grid
        '''
        grid = deepcopy(self.grid)
        grid[row_index][col_index]["stone"] = plyr_color
        # update each direction's number of same stone color sequence on the given position(row_index, col_index)
        for direct in ['right', 'down', 'SE', 'SW']:
            grid[row_index][col_index][direct] += 1

        # update the nearby positions if they have same color of stone as given position on it
        if (col_index + 1 < 15) and grid[row_index][col_index + 1]["stone"] == plyr_color:
                grid[row_index][col_index]['right'] += grid[row_index][col_index + 1]['right']
        # update down of current location
        if (row_index + 1 < 15) and grid[row_index + 1][col_index]["stone"] == plyr_color:
                grid[row_index][col_index]['down'] += grid[row_index + 1][col_index]['down']
        # update SE of current location, and SE for NW stones of current location
        if (row_index + 1 < 15 and col_index + 1 < 15) and grid[row_index + 1][col_index + 1]["stone"] == plyr_color:
                grid[row_index][col_index]['SE'] += grid[row_index + 1][col_index + 1]['SE']
        # update SW of current location
        if (row_index + 1 < 15 and col_index - 1 >= 0) and grid[row_index + 1][col_index - 1]["stone"] == plyr_color:
                grid[row_index][col_index]['SW'] += grid[row_index + 1][col_index - 1]['SW']
        # update adjacent stones
        for indx in range(1, 5):
            if (col_index - indx >= 0) and grid[row_index][col_index - indx]["stone"] == plyr_color:
                if grid[row_index][col_index - indx]['right'] >= indx:
                    grid[row_index][col_index - indx]['right'] += grid[row_index][col_index]['right']
            if (row_index - indx >= 0) and grid[row_index - indx][col_index]["stone"] == plyr_color:
                if grid[row_index - indx][col_index]['down'] >= indx:
                    grid[row_index - indx][col_index]['down'] += grid[row_index][col_index]['down']
            if (row_index - indx >= 0 and col_index - indx >= 0) and \
                    grid[row_index - indx][col_index - indx]["stone"] == plyr_color:
                if grid[row_index - indx][col_index - indx]['SE'] >= indx:
                    grid[row_index - indx][col_index - indx]['SE'] += grid[row_index][col_index]['SE']
            if (row_index - indx >= 0 and 0 <= col_index + indx < 15) and \
                    grid[row_index - indx][col_index + indx]["stone"] == plyr_color:
                if grid[row_index - indx][col_index + indx]['SW'] >= indx:
                    grid[row_index - indx][col_index + indx]['SW'] += grid[row_index][col_index]['SW']
        return grid

    def can_move(self, row_ind, col_ind, plyr_color):
        '''
        player should not place a stone in a position that already have a stone
        nor in a position that creates two open rows with three consecutive three stones
        :param player: current player(aka stone color)
        :return: type: string, True if legal move, or otherwise error message
        '''
        if self.grid[row_ind][col_ind]["stone"] is not None: return False, "There is another stone in that place"
        alternate_grid = self.update_grid(row_ind, col_ind, plyr_color)

        # tre_dict is used to find a sequence with three same color stone to check rule of three-three violation
        tre_dict = {'right': set(), 'down': set(), 'SE': set(),
                    'SW': set()}  # Key: direction, Val: set of sequences of three
        opponent = abs(plyr_color - 1)
        direction_sign_translator = {"right": (0, 1), "down": (1, 0), "SE": (1, 1), "SW": (1, -1)}
        for i in range(-2, 3):
            for j in range(-2, 3):
                try:
                    r = row_ind + i
                    c = col_ind + j
                    if alternate_grid[row_ind + i][col_ind + j]["stone"] == plyr_color:
                        for direction in ("right", "down", "SE", "SW"):
                            if alternate_grid[row_ind + i][col_ind + j][direction] == 3:
                                r_sign, c_sign = direction_sign_translator[direction]  # row and column sign
                                one_next_valid, three_next_valid = False, False
                                if (0 <= row_ind + i - 1*r_sign) and (0 <= col_ind + j - 1*c_sign):
                                    one_next_valid = True  # row+-1 and column+-1 not out of index
                                if (0 <= row_ind + i + 3*r_sign < 15) and (0 <= col_ind + j + 3*c_sign < 15):
                                    three_next_valid = True
                                is_sequence_three, one_next_opened, three_next_opened = False, False, False
                                if one_next_valid:
                                    if alternate_grid[row_ind + i - 1 * r_sign][col_ind + j - 1 * c_sign]["stone"] != opponent:
                                        one_next_opened = True
                                    if alternate_grid[row_ind + i - 1*r_sign][col_ind + j - 1*c_sign][direction] < 4:
                                        is_sequence_three = True
                                if three_next_valid:
                                    if alternate_grid[row_ind + i + 3*r_sign][col_ind + j + 3*c_sign]["stone"] != opponent:
                                        three_next_opened = True
                                # to check whether the sequence is blocked in both sides
                                if is_sequence_three and (one_next_opened and three_next_opened):
                                        for k in range(0, 3):
                                            tre_dict[direction].add((row_ind + i+ k*r_sign, col_ind + j + k*c_sign))
                except IndexError:
                    continue
        tre_count = 0
        is_current_loc = False
        curr_move_direct = None
        for key in tre_dict.keys():
            if (row_ind, col_ind) in tre_dict[key]:
                # only need to one direction even if the current move occurred in different directions
                curr_move_direct = key  # the assumption is that the violation can only occur by the current move
                break
        if curr_move_direct is not None:
            for key in tre_dict.keys():
                without_redundancy = tre_dict[key] - tre_dict[curr_move_direct]
                if len(without_redundancy) < len(tre_dict[key]):
                    tre_count += (len(tre_dict[key])+2)//3  # rounding up to account for redundancy within the set
        del alternate_grid
        if tre_count >= 2:
            return False, "you violated the rule of three-three"
        return True, ""

    def move(self, row_index, col_index, player):
        '''
        place the stone in the requested position if it's possible
        :param player: current player
        :return: True if successfully set or False if unsuccessful
        '''
        self.grid = self.update_grid(row_index, col_index, player)
        self.whose_turn = abs(self.whose_turn - 1)
        self.turns += 1


    def win(self, row_index, col_index):
        # return true if same stone in a five successive row
        for num_stone in self.grid[row_index][col_index].values():
            if num_stone == 5: return True
        skip_lst = [(0, 0), (0, 1)]
        r_lst, c_lst = [-1, 0], [-1, 0, 1]
        for ind in range(1, 5):
            for r_sign in r_lst:
                for c_sign in c_lst:
                    if (r_sign, c_sign) in skip_lst: continue
                    curr_row, curr_col = row_index + r_sign * ind, col_index + c_sign * ind
                    if not 0 <= curr_row < 15 and r_sign in r_lst: r_lst.remove(r_sign)
                    if not 0 <= curr_col < 15 and c_sign in c_lst: c_lst.remove(c_sign)
                    if 0 <= curr_row < 15 and 0 <= curr_col < 15:
                        direct = direction_translator[str(r_sign)+str(c_sign)]
                        if self.grid[curr_row][curr_col]["stone"] != self.grid[row_index][col_index]["stone"]:
                            skip_lst.append((r_sign, c_sign))  # no same color implies no row of 5 along the search
                        if self.grid[curr_row][curr_col][direct] == 5: return True
        if self.turns == 225: return None  # this is a draw
        return False


if __name__ == '__main__':
    g = Gomoku()
    g.move(0,4,1)
    g.move(1,4,0)
    g.move(1,3,1)
    g.move(2,4,0)
    g.move(2,3,1)
    g.move(2,5,1)
    g.move(3,4,0)
    g.move(3,5,0)
    g.move(3,3,1)
    g.move(4,4,0)
    g.move(4,3,0)
    g.move(4,1,1)
    g.move(5,2,0)
    g.move(5,4,1)
    g.move(6,3,0)
    g.move(7,4,1)
    print(g)
    print(g.can_move(5,3,0))