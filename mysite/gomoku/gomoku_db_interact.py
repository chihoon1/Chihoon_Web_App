'''
This python script is used for gomoku app to get from or add data directly to database
'''
import sqlite3

# the commented imports should be used for test.py instead of the uncommented ones
'''
# also don't forget to use the commented imports in stock_db_interact.py, gomoku_engine.py and Computer_Player.py
from Computer_Player import *
from mysite.stock_db_interact import decode_json_in_row
from mysite.stockmarket.operation_functions import convert_to_json
'''
from .Computer_Player import *
from stock_db_interact import decode_json_in_row
from stockmarket.operation_functions import convert_to_json


def get_table_name(data_type, db_name='db.sqlite3'):
    conn = sqlite3.connect(db_name)
    select_cmd = "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%" + data_type.lower() + "%';"
    table_name = conn.execute(select_cmd).fetchone()[0]
    # print(table_name)
    conn.commit()
    conn.close()
    return table_name


def add_gomoku_row(table_name, db_name='db.sqlite3', *fields_values):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    prev_row = select_row(table_name, db_name, None, "Max(ROWID)")
    prev_rowid = 0 if len(prev_row) < 1 or prev_row[0] is None else prev_row[0]
    rowid = int(prev_rowid) + 1
    gomoku = Gomoku()

    # make a first move by computer player if computer player's stone is black
    try:
        computer_stone_color = fields_values[4]
        if computer_stone_color == 1:
            plyr_stone_color = int(fields_values[2])
            human_plyr = Player(fields_values[1], plyr_stone_color)
            computer_stone_color = int(computer_stone_color)
            difficulty = 'easy'  # this doesn't really matter since the initial move is same for every game
            computer_plyr = AIPlayer(computer_stone_color, difficulty.lower())
            run_game(gomoku, (7, 7), computer_plyr, human_plyr)
    except IndexError:
        pass
    tup_json = (rowid,
                convert_to_json(gomoku.grid),
                convert_to_json(gomoku.turns),
                convert_to_json(gomoku.whose_turn),
                convert_to_json(fields_values[0]),
                convert_to_json(fields_values[1]),
                convert_to_json(fields_values[2]),
                convert_to_json(fields_values[3]),
                convert_to_json(fields_values[4]),
                )
    cursor.execute("INSERT INTO " + table_name + " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);", tup_json)
    # print("new Gomoku data added")
    conn.commit()
    conn.close()
    return rowid


def select_row(table_name: str, db_name='db.sqlite3', rowid=None,  *fields):
    # return a row in a given table
    # if rowid is given, then the row with the given id will be selected
    conn = sqlite3.connect(db_name)
    if len(fields) == 1 and type(fields[0]) == tuple:
        # this will be True only when this functions is called by another function that uses *args
        fields = fields[0]
    if len(fields) > 0:
        query_fields_str = ""
        for i in range(len(fields)):
            query_fields_str += fields[i]
            if i < (len(fields) - 1): query_fields_str += ", "
    else:
        query_fields_str = "*"
    select_cmd = "SELECT " + query_fields_str + " FROM " + table_name
    if rowid is not None: select_cmd += " WHERE ROWID = " + str(rowid)
    row = conn.execute(select_cmd + ";").fetchone()
    conn.commit()
    conn.close()
    if len(row) == 1 and None in row:
        return row
    else:
        return decode_json_in_row(row)


def update_gomoku_row(table_name, row_id, fields_dict, db_name='db.sqlite3'):
    # expected fields in the fields_dict(Ordered dict Param): grid, number_turns, whose_turn, difficulty_level,
    # player1_name, player1_color, player2_name, player2_color
    # If not updating a certain field, then assign None as its value
    # return the rowid of the updated row
    conn = sqlite3.connect(db_name)
    rowid_str = str(row_id)
    updated_fields_lst = []
    query_fields_str = ""
    count = 0
    for key, value in fields_dict.items():
        count += 1
        if value is not None:
            updated_fields_lst.append(convert_to_json(value))
            query_fields_str += key + " = ?, "
    query_fields_str = query_fields_str[:-2]  # remove the comma and space after the last field name
    tup_json = tuple(updated_fields_lst)
    updated_cmd = "UPDATE " + table_name + " SET " + query_fields_str + " WHERE ROWID = " + rowid_str
    conn.execute(updated_cmd + ";", tup_json)

    conn.commit()
    conn.close()
    return row_id


def delete_specific_row(table_name, row_id, db_name='db.sqlite3'):
    # delete the row with the given row id in the given table, and return nothing
    conn = sqlite3.connect(db_name)
    conn.execute("DELETE FROM " + table_name + " WHERE ROWID = " + str(row_id) + ";")
    conn.commit()
    conn.close()


# this below part is designated for the functions for game running
def main_running(table_name: str, row_id: int, plyr_action: tuple, db_name='db.sqlite3'):
    # run the game by playing the move(plyr_action Parameter) given by the player
    # return a dictionary. key = one of error, winner, or Gomoku, and the value is the corresponding value

    # create Gomoku and corresponding Player classes, using the field values stored in the database
    gomoku_row = select_row(table_name, db_name, row_id)
    plyr_stone_color = int(gomoku_row[6])
    human_plyr = Player(gomoku_row[5], plyr_stone_color)
    computer_stone_color = int(gomoku_row[8])
    difficulty = gomoku_row[4]
    computer_plyr = AIPlayer(computer_stone_color, difficulty.lower())
    gomoku_game = Gomoku(turns=gomoku_row[2], player1=plyr_stone_color, player2=computer_stone_color)
    gomoku_game.grid = gomoku_row[1]
    gomoku_game.whose_turn = gomoku_row[3]

    # try the move on the board and gives error message if move is not valid
    move = (int(plyr_action[0]), int(plyr_action[1]))
    move_validity = run_game(gomoku_game, move, human_plyr, computer_plyr)
    result_dict = {}
    if not move_validity[0]:
        result_dict['error'] = move_validity[1]
    elif move_validity[0] == 2:
        result_dict['winner'] = "You Won!"
    else:
        computer_move = computer_plyr.ABPruning(gomoku_game, move)[1]
        # print(computer_move)
        any_winner = run_game(gomoku_game, computer_move, computer_plyr, human_plyr)
        if any_winner[0] == 2:
            result_dict['winner'] = "Computer Won..."
            result_dict['computer_move'] = computer_move
        else:
            result_dict['gomoku'] = gomoku_game
    return result_dict


def run_game(gomoku: Gomoku, move: tuple, player, opponent):
    # This will be called after human player makes a move
    # returns 0(if can't move), 1(can move), 2(winner decided) with corresponding message
    validity = gomoku.can_move(move[0], move[1], player.player_color)
    if not validity[0]:
        return validity
    else:
        gomoku.move(move[0], move[1], player.player_color)
        any_winner = gomoku.win(move[0], move[1])
        if any_winner:
            return 2, "won"
        elif any_winner is None:
            return 2, "Draw. You both tied."
        return validity
