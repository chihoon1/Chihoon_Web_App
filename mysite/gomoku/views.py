from random import randrange
from collections import OrderedDict

from django.shortcuts import render
from django.views.generic import View
from django.urls import reverse
from django.http import HttpResponseRedirect

from .gomoku_db_interact import *


# Create your views here.
class MainView(View):
    context = {}
    template_name = "gomoku/gomoku_main.html"

    def get(self, request):
        context = self.context
        return render(request, self.template_name, context)

    def post(self, request):
        if request.POST['play'] == 'play':
            return HttpResponseRedirect(reverse("gomoku:select-difficulty-page"))


class DifficultyView(View):
    context= {}
    template_name = "gomoku/select_difficutly.html"

    def get(self, request):
        context = self.context
        player_stone_color = randrange(2)
        computer_stone_color = abs(1 - player_stone_color)
        context['player_stone_color'] = "black" if player_stone_color else "white"
        context['computer_stone_color'] = "black" if computer_stone_color else "white"
        # create a row in gomoku table but only store player names and stone colors
        table_name = get_table_name('gomoku', 'gomoku/gomoku_db.sqlite3')
        row_id = add_gomoku_row(table_name, 'gomoku/gomoku_db.sqlite3', None,
                               "Anonymous User", player_stone_color, "Computer", computer_stone_color)
        request.session['gomoku_game_id'] = row_id
        request.session['gomoku_table_name'] = table_name
        return render(request, self.template_name, context)

    def post(self, request):
        if 'difficulty' in request.POST:
            fields_dict = initialize_fields_ordered_dict()
            fields_dict['difficulty_level'] = request.POST['difficulty']
            table_name = request.session['gomoku_table_name']
            row_id = request.session['gomoku_game_id']
            row_id = update_gomoku_row(table_name, row_id, fields_dict, 'gomoku/gomoku_db.sqlite3')
            request.session['gomoku_game_id'] = row_id
            return HttpResponseRedirect(reverse("gomoku:play-page"))


def initialize_fields_ordered_dict():
    fields_dict = OrderedDict()
    none_value_fields_lst = ['grid', 'number_turns', 'whose_turn', 'difficulty_level',
                             'player1_name', 'player1_color', 'player2_name', 'player2_color']
    for elem in none_value_fields_lst:
        fields_dict[elem] = None
    return fields_dict

class PlayView(View):
    context = {}
    template_name = "gomoku/gomoku_play.html"

    def get(self, request):
        context = {}
        try:
            row_id = request.session['gomoku_game_id']
            table_name = request.session['gomoku_table_name']
        except KeyError:  # this is expected to occur when row id or table name is not in the session
            context['invalid_access'] = "Go Back to the Gomoku Main Page and "
            context['invalid_access'] += "Start playing the game by selecting the difficulty"
            return render(request, self.template_name, context)
        if request.session.get('player_move'):
            move = request.session['player_move']
            result_dict = main_running(table_name, row_id, move, 'gomoku/gomoku_db.sqlite3')
            print("result dict: ", result_dict)
            if result_dict.get('error'):
                context['game_run_message'] = result_dict['error']
                context['second_game_run_message'] = "Please place the stone in somewhere else"
            if result_dict.get('winner'):
                context['second_game_run_message'] = result_dict['winner']
                context['any_winner'] = True
            if result_dict.get('gomoku'):
                gomoku_state = result_dict['gomoku']
                # update the gomoku row with the new state on the game board
                fields_dict = initialize_fields_ordered_dict()
                fields_dict['grid'] = gomoku_state.grid
                fields_dict['number_turns'] = gomoku_state.turns
                fields_dict['whose_turn'] = gomoku_state.whose_turn
                row_id = update_gomoku_row(table_name, int(row_id), fields_dict, 'gomoku/gomoku_db.sqlite3')
        gomoku_row = select_row(table_name, 'gomoku/gomoku_db.sqlite3', row_id)
        gomoku_grid = gomoku_row[1]
        try:  # this try block is to update the board to show the row of five winning stones on the board
            if result_dict.get('winner'):
                plyr_color = gomoku_row[6]
                gomoku_state = Gomoku()
                gomoku_state.grid = gomoku_grid
                gomoku_state.move(int(move[0]), int(move[1]), plyr_color)
                if 'computer' in result_dict.get('winner').lower():
                    move = result_dict.get('computer_move')
                    plyr_color = abs(1 - plyr_color)
                    gomoku_state.move(int(move[0]), int(move[1]), plyr_color)
                gomoku_grid = gomoku_state.grid
        except NameError:
            pass
        request.session['player_move'] = None
        current_board = []
        non_null_count = 0
        for i in range(15):
            row_lst = []
            for j in range(15):
                col_i = gomoku_grid[j][i]  # html inblock is vertical, so the make list stores a column in inner list
                location = str(j) + "," + str(i)
                if col_i['stone'] is None:
                    stone = -1  # -1 represent no stone at the location
                else:
                    stone = col_i['stone']
                    non_null_count += 1
                loc_stone_dict = {location: stone}
                row_lst.append(loc_stone_dict)
            current_board.append(row_lst)
        num_of_turns = gomoku_row[2]
        if non_null_count > 0 and num_of_turns == 0: context['game_run_message'] = "Computer made the First Move"
        context['current_board'] = current_board
        context['your_stone_color'] = "Black" if gomoku_row[6] else "White"
        context['computer_stone_color'] = "Black" if gomoku_row[8] else "White"
        return render(request, self.template_name, context)

    def post(self, request):
        if request.POST.get('reset') == 'reset' or request.POST.get('end_game') == 'end_game':
            # print("DELETED the ROW")
            table_name = request.session['gomoku_table_name']
            row_id = request.session['gomoku_game_id']
            delete_specific_row(table_name, row_id, 'gomoku/gomoku_db.sqlite3')
            if request.POST.get('reset') == 'reset':
                return HttpResponseRedirect(reverse("gomoku:select-difficulty-page"))
            else:
                return HttpResponseRedirect(reverse("gomoku:main-page"))
        if request.POST.get('player_move') is not None:
            move_str = request.POST['player_move']
            # print(f"POST: {move_str}")
            move_x, move_y = move_str.split(',')
            move_tup = (int(move_x), int(move_y))
            request.session['player_move'] = move_tup
            return HttpResponseRedirect(reverse("gomoku:play-page"))