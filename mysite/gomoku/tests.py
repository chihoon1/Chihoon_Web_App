from collections import OrderedDict

from django.test import TestCase
from gomoku_db_interact import *
from create_gomoku_db import *

# Create your tests here.
def test_create_gomoku_row(db_name):
    table_name = get_table_name('gomoku', 'test.db')
    rowid = add_gomoku_row(table_name, 'test.db', None, None, None, None, "testing")
    row = select_row(table_name, 'test.db', rowid)
    assert len(row) == 9
    rowid = add_gomoku_row(table_name, 'test.db', None, None, 0, None, 1)
    row = select_row(table_name, 'test.db', rowid)
    print(row[1][7][7]['stone'])
    assert len(row) == 9
    assert row[1][7][7]['stone'] == 1



def test_update_gomoku_row(db_name):
    fields_dict = OrderedDict()
    none_value_fields_lst = ['grid', 'number_turns', 'whose_turn', 'difficulty_level',
                             'player1_name', 'player1_color', 'player2_name', 'player2_color']
    for elem in none_value_fields_lst:
        fields_dict[elem] = None
    fields_dict['difficulty_level'] = 'medium'
    table_name = get_table_name('gomoku', 'test.db')
    rowid = select_row(table_name, db_name, None, "Max(ROWID)")[0]
    rowid = update_gomoku_row(table_name, int(rowid), fields_dict, db_name)
    row = select_row(table_name, 'test.db', rowid)
    assert row[4] == 'medium'
    fields_dict['difficulty_level'] = None
    fields_dict['player1_name'] = "Chihoon"
    fields_dict['player1_color'] = 0
    fields_dict['player2_name'] = "Computer"
    fields_dict['player2_color'] = 1
    rowid = update_gomoku_row(table_name, int(rowid), fields_dict, db_name)
    row = select_row(table_name, 'test.db', rowid)
    assert row[5] == "Chihoon"


def test_delete(db_name):
    table_name = get_table_name('gomoku', 'test.db')
    rowid = select_row(table_name, db_name, None, "Max(ROWID)")[0]
    delete_specific_row(table_name, rowid, db_name)
    next_rowid = select_row(table_name, db_name, None, "Max(ROWID)")[0]
    assert int(rowid) == (int(next_rowid) - 1)


def test_game_run(db_name='test.db'):
    # setting some of the required fields of gomoku row before testing
    table_name = get_table_name('gomoku', db_name)
    rowid = select_row(table_name, db_name, None, "Max(ROWID)")[0]
    fields_dict = OrderedDict()
    none_value_fields_lst = ['grid', 'number_turns', 'whose_turn', 'difficulty_level',
                             'player1_name', 'player1_color', 'player2_name', 'player2_color']
    for elem in none_value_fields_lst:
        fields_dict[elem] = None
    fields_dict['difficulty_level'] = 'easy'
    rowid = update_gomoku_row(table_name, int(rowid), fields_dict, db_name)

    # valid move
    result_dict = main_running(table_name, rowid, (3, 4), db_name)
    gomoku_state = result_dict['gomoku']
    print(gomoku_state)
    assert gomoku_state.grid[3][4]['stone'] == 0
    # update the gomoku row with the new state on the game board
    fields_dict['grid'] = gomoku_state.grid
    fields_dict['number_turns'] = gomoku_state.turns
    fields_dict['whose_turn'] = gomoku_state.whose_turn
    rowid = update_gomoku_row(table_name, int(rowid), fields_dict, db_name)
    # invalid - placing stone at the location where there is already another stone
    result_dict = main_running(table_name, rowid, (3, 4), db_name)
    error = result_dict['error']
    print(error)
    assert type(error) == str
    # testing three-three violation
    gomoku = Gomoku()
    for i in range(3, 6):
        gomoku.move(i, 3, 0)
    gomoku.move(3, 4, 0)
    validity = gomoku.can_move(3, 5, 0)
    print(validity[1])
    assert validity[0] == False

if __name__ == '__main__':
    # create_gomoku_table('test.db')  # do this first if test.db doesn't exist
    test_create_gomoku_row('test.db')
    test_update_gomoku_row('test.db')
    test_delete('test.db')
    test_game_run()

