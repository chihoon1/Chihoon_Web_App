import datetime
from copy import deepcopy

from django.shortcuts import render
from django.views.generic import View
from django.urls import reverse
from django.http import HttpResponseRedirect
import numpy as np

from stock_db_interact import *
from .models import MacroEconomy, Stock
from .operation_functions import *
from .macro_economy import MacroEcon
from .stockmarket_predictor import *


# Create your views here.
def add_econ_data_to_context():
    context = {}
    macro_econ_data = fetch_the_latest_data("MacroEconomy", "stockmarket/stockmarket_db.sqlite3")
    delete_rows('stockmarket_macroeconomy', 5, db_name="stockmarket/stockmarket_db.sqlite3")
    key_list = ['time', 'fed_rate', 'longterm_treasury_yield', 'inflation_rate',
                'unemployment_rate', 'gdp', 'vix']
    for i in range(1, len(macro_econ_data)):
        elem = macro_econ_data[i]
        if type(elem) != list:
            elem = str(elem)
            context[key_list[i - 1]] = elem
        else:
            context[key_list[i - 1]] = elem[0][1]
    context['predict_options'] = ["Fed Interest Rate"]
    return context


class MainView(View):
    template_name = "stockmarket/face_page.html"
    model = MacroEconomy
    context = {}
    context["stock_graph_options"] = None

    def get(self, request, *args, **kwargs):
        if request.session.get('econ data') is not None:
            data_time = datetime.datetime.strptime(request.session['econ data']['time'], "%Y-%m-%d %H:%M:%S.%f")
            curr_time = datetime.datetime.now()
            time_diff = curr_time - data_time
            if time_diff >= datetime.timedelta(hours=12):
                request.session['econ data'] = add_econ_data_to_context()
        else:
            request.session['econ data'] = add_econ_data_to_context()
        self.context = request.session['econ data']
        context = {}
        context = deepcopy(self.context)
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        if "graph-options" in request.POST:
            request.session['graph'] = request.POST['graph-options']
            return HttpResponseRedirect(reverse("stockmarket:graph-page"))
        if "company-name" in request.POST:
            request.session['company name'] = request.POST['company-name']
            return HttpResponseRedirect(reverse("stockmarket:ticker-page"))
        if 'predictor-selection' in request.POST:
            request.session['predictor'] = request.POST['predictor-selection']
            return HttpResponseRedirect(reverse("stockmarket:predictor-page"))
        return render(request, "stock_main_page.html")


class GraphView(View):
    template_name = "stockmarket/graph_page.html"
    context = {}

    def get(self, request, *args, **kwargs):
        if request.session.get('econ data') is not None:
            data_time = datetime.datetime.strptime(request.session['econ data']['time'], "%Y-%m-%d %H:%M:%S.%f")
            curr_time = datetime.datetime.now()
            time_diff = curr_time - data_time
            if time_diff >= datetime.timedelta(hours=12):
                request.session['econ data'] = add_econ_data_to_context()
        else:
            request.session['econ data'] = add_econ_data_to_context()
        self.context = request.session['econ data']
        context = {}
        context = deepcopy(self.context)
        graph_option = request.session.get('graph')
        graph_img = get_graph_image(graph_option)
        if type(graph_img) != str:  # Error: graph option was not given by the user
            context['error_message'] = graph_img
        else:
            context['chart'] = graph_img
        return render(request, self.template_name, context)

    def post(self, request):
        if 'predictor-selection' in request.POST:
            request.session['predictor'] = request.POST['predictor-selection']
            return HttpResponseRedirect(reverse("stockmarket:predictor-page"))
        request.session['graph'] = request.POST['graph-options']
        return HttpResponseRedirect(reverse("stockmarket:graph-page"))


def get_graph_image(graph_option):
    graph_tool = GraphTool()
    if graph_option == "fed-rate":
        fed_rate = fetch_the_latest_data("MacroEconomy", "stockmarket/stockmarket_db.sqlite3", "fed_rate")[0]
        days, rates, x_tick, time_interval = get_x_y_axis_data(fed_rate, "years")
        graph_tool.graph_with_one_y(days, rates, x_tick, "Federal interest Rate", "Date", "Fed Rate(%)")
        return graph_tool.graph_img
    elif graph_option == "treasury-yield":
        treasury_yields = fetch_the_latest_data("MacroEconomy", "stockmarket/stockmarket_db.sqlite3", "longterm_treasury_yield")[0]
        days, yields, x_tick, time_interval = get_x_y_axis_data(treasury_yields, "years")
        graph_tool.graph_with_one_y(days, yields, x_tick, "Longterm Treasury Yield", "Date", "Treasury Yields(%)", 0.5)
        return graph_tool.graph_img
    elif graph_option == "inflation-rate":
        inflation_rates = fetch_the_latest_data("MacroEconomy", "stockmarket/stockmarket_db.sqlite3", "inflation_rate")[0]
        days, rates, x_tick, time_interval = get_x_y_axis_data(inflation_rates, "years")
        graph_tool.graph_with_one_y(days, rates, x_tick, "Inflation Rate", "Date", "Inflation(%)", 0.5)
        return graph_tool.graph_img
    elif graph_option == "unemployment-rate":
        unemployment_rate = fetch_the_latest_data("MacroEconomy", "stockmarket/stockmarket_db.sqlite3", "unemployment_rate")[0]
        days, rates, x_tick, time_interval = get_x_y_axis_data(unemployment_rate, "years")
        graph_tool.graph_with_one_y(days, rates, x_tick, "Unemployment Rate", "Date", "Rate(%)", 0.5)
        return graph_tool.graph_img
    elif graph_option == "gdp":
        gdp = fetch_the_latest_data("MacroEconomy", "stockmarket/stockmarket_db.sqlite3", "gdp")[0]
        days, rates, x_tick, time_interval = get_x_y_axis_data(gdp, "quarters", override=True)
        graph_tool.graph_with_one_y(days, rates, x_tick, "Quarterly GDP growth", "Date", "Rate(%)", 0.5)
        return graph_tool.graph_img
    elif graph_option == "stock-price":
        return
    elif graph_option == "volume":
        return
    elif graph_option == "dividends":
        return
    elif graph_option == "stock-splits":
        return
    else:
        return "No input given"


class TickerView(View):
    context = {}
    template_name = "stockmarket/ticker_page.html"

    def get(self, request):
        context = {}
        if request.session.get('econ data') is not None:
            data_time = datetime.datetime.strptime(request.session['econ data']['time'], "%Y-%m-%d %H:%M:%S.%f")
            curr_time = datetime.datetime.now()
            time_diff = curr_time - data_time
            if time_diff >= datetime.timedelta(hours=12):
                request.session['econ data'] = add_econ_data_to_context()
        else:
            request.session['econ data'] = add_econ_data_to_context()
        self.context = request.session['econ data']
        context = deepcopy(self.context)
        if request.session.get('company name'):
            stock = create_stock(request.session['company name'])
            try:
                possible_tickers_dict = find_ticker(stock)
                if type(possible_tickers_dict) == str: context['api_error'] = possible_tickers_dict
                else: context['tickers'] = possible_tickers_dict
            except TypeError:  # this error will happen when the company name has no publicly listed stock
                context['api_error'] = "There is no stock listed with the given company name." \
                        + "\nTry with different name."
            return render(request, self.template_name, context)
        else:
            return HttpResponseRedirect(reverse("stockmarket:main-page"))

    def post(self, request):
        if "ticker-selection" in request.POST:
            ticker_selection_str = request.POST['ticker-selection']
            stock_name, ticker = ticker_selection_str.split(":")
            request.session['ticker'] = (stock_name, ticker)
            return HttpResponseRedirect(reverse("stockmarket:stock-page"))
        if 'predictor-selection' in request.POST:
            request.session['predictor'] = request.POST['predictor-selection']
            return HttpResponseRedirect(reverse("stockmarket:predictor-page"))
        if request.POST.get('graph-options'):
            request.session['graph'] = request.POST['graph-options']
            return HttpResponseRedirect(reverse("stockmarket:graph-page"))
        return HttpResponseRedirect(reverse("stockmarket:main-page"))


class StockView(View):
    template_name = "stockmarket/stock_page.html"
    context = {}

    def get(self, request):
        context = {}
        if request.session.get('econ data') is not None:
            data_time = datetime.datetime.strptime(request.session['econ data']['time'], "%Y-%m-%d %H:%M:%S.%f")
            curr_time = datetime.datetime.now()
            time_diff = curr_time - data_time
            if time_diff >= datetime.timedelta(days=1): request.session['econ data'] = add_econ_data_to_context()
        else:
            request.session['econ data'] = add_econ_data_to_context()
        self.context = request.session['econ data']
        context = deepcopy(self.context)
        if request.session.get('ticker'):
            stock_name, ticker = request.session['ticker']
            context['stock_name'] = stock_name
            context['stock_ticker'] = ticker
            stock = create_stock(stock_name, ticker)
            # use yahooquery
            stock.get_stock_data()
            if type(stock.stock_data) == str: context['api_error'] = stock.stock_data
            else: context['today_stock_data'] = stock.stock_data
            stock.get_recent_financials()
            if type(stock.financials) == str: context['financials_error'] = stock.financials
            else: context['financials'] = stock.financials
        else:
            context['page_error'] = "No ticker is given. Go back to the app's main page and search for one."
        return render(request, self.template_name, context)

    def post(self, request):
        if 'predictor-selection' in request.POST:
            request.session['predictor'] = request.POST['predictor-selection']
            return HttpResponseRedirect(reverse("stockmarket:predictor-page"))
        if request.POST.get('graph-options'):
            request.session['graph'] = request.POST['graph-options']
            return HttpResponseRedirect(reverse("stockmarket:graph-page"))
        return render(request, self.template_name, self.context)


class PredictView(View):
    # warning: data for predictor table in database should be added through stockmarket_predictor_database_function.py
    template_name = "stockmarket/predictor.html"
    context = {}

    def get(self, request):
        if request.session.get('econ data') is not None:
            data_time = datetime.datetime.strptime(request.session['econ data']['time'], "%Y-%m-%d %H:%M:%S.%f")
            curr_time = datetime.datetime.now()
            time_diff = curr_time - data_time
            if time_diff >= datetime.timedelta(hours=12):
                request.session['econ data'] = add_econ_data_to_context()
        else:
            request.session['econ data'] = add_econ_data_to_context()
        self.context = request.session['econ data']
        context = deepcopy(self.context)
        econ = MacroEcon(empty_instance=True)
        predict_option = request.session.get('predictor')
        if predict_option:
            if predict_option == 'Fed Interest Rate' or "fed_rate":
                # get all the data needed to run the class predictor functions
                fed_rate, inflation_rate = fetch_the_latest_data("MacroEconomy", "stockmarket/stockmarket_db.sqlite3",
                                                                 "fed_rate", "inflation_rate")
                monthly_fed = convert_data_by_given_interval(fed_rate)
                latest_data_date = datetime.datetime.strptime(fed_rate[0][0], "%Y-%m-%d")
                if latest_data_date.day != 1: monthly_fed = monthly_fed[1:]
                prev_fed_rate = monthly_fed[-1]
                curr_inflation = econ.get_current_month_inflation()
                predictor_data = fetch_latest_predictor_data('fed_rate', "stockmarket/stockmarket_db.sqlite3")
                initial_prob, transition_prob, emission_prob = predictor_data[3], predictor_data[4], predictor_data[5]
                # predict the future state with Viterbi algorithm
                predictor = PredictHMM('fed_rate', initial_prob, transition_prob, emission_prob)
                result_tuple = predictor.predict_fed_rate(monthly_fed, inflation_rate, curr_inflation, False)
                most_probable_state, interests, inflations, state_space, emission_space, model = result_tuple
                # graph with fed rates and inflation rates as y axes
                days, fed_rates_axis, x_tick, time_interval = get_x_y_axis_data(interests, override=True)
                inflation_axis = get_x_y_axis_data(inflations, override=True)[1]
                graph_tool = GraphTool()
                title = "Fed Rates(left) and Inflation Rates(right) graph"
                y_labels = ("Fed Rates(%)", "Inflation Rates(%)")
                y_ticks = (np.array(state_space), np.array(emission_space))
                graph_img = graph_tool.graph_with_two_y(days, x_tick, title, "Dates", y_labels, y_ticks,
                                                        fed_rates_axis, inflation_axis)
                chart_info = "The end points in Y axes represent 'Greater than or Equal to' or 'Less than or Equal to'."
                algo_info = "\nThe future state(marked blue in the graph) is predicted by using Hidden Markov Model."
                algo_detail_info = "\nHidden State: " + "Fed Rates" + ", Emission/Observation: " + "Inflation Rates"
                context['additional_message'] = [chart_info, algo_info, algo_detail_info]
                context['chart'] = graph_img
                context['next_date'] = days[-1]
                context['most_probable_state'] = str(most_probable_state) + "%"
                context['hidden_state'] = 'Fed Interest Rate'
        else:
            context['error_message'] = "You haven't chosen the data to be predicted"
        return render(request, self.template_name, context)

    def post(self, request):
        if 'predictor-selection' in request.POST:
            request.session['predictor'] = request.POST['predictor-selection']
            return HttpResponseRedirect(reverse("stockmarket:predictor-page"))
        if request.POST.get('graph-options'):
            request.session['graph'] = request.POST['graph-options']
            return HttpResponseRedirect(reverse("stockmarket:graph-page"))
        return render(request, self.template_name, self.context)


