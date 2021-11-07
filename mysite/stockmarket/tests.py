import datetime

from django.test import TestCase
import sqlite3

from mysite.stock_db_interact import *
from mysite.stockmarket.operation_functions import *
from mysite.stockmarket.stockmarket_predictor import *


# Create your tests here.
def create_test_db():
    conn = sqlite3.connect("test.db")
    conn.execute("CREATE TABLE stockmarket_MacroEconomy ( rowid INTEGER, \
                    timestamp Text, \
                    fed_rate TEXT, \
                    longterm_treasury_yield TEXT, \
                    inflation_rate TEXT, \
                    unemployment_rate TEXT, \
                    gdp TEXT, \
                    vix TEXT);")
    conn.execute("CREATE TABLE stockmarket_Stock ( rowid INTEGER,\
                    company TEXT, \
                    ticker TEXT, \
                    stock_price TEXT, \
                    dividends TEXT, \
                    volume TEXT, \
                    stock_splits TEXT, \
                    interval TEXT, \
                    financials  TEXT);")
    conn.execute("CREATE TABLE stockmarket_Predictor ( rowid INTEGER,\
                        type TEXT, \
                        timestamp TEXT, \
                        initial_probabilities TEXT, \
                        transition_probabilities TEXT, \
                        emission_probabilities TEXT, \
                        state_space TEXT, \
                        emission_space TEXT);")
    conn.commit()
    conn.close()


def test_econ_initialization(true_vix_index=None):
    # true_vix_index is the vix index found in https://finance.yahoo.com/quote/%5EVIX/
    # if you don't want to search for the vix index in that url, don't need to pass any parameter
    macro_economy = MacroEcon()
    assert (type(macro_economy.time) == datetime.datetime)
    assert (len(macro_economy.interest_rate) > 0)
    assert (len(macro_economy.longterm_treasury) > 0)
    assert (len(macro_economy.inflation_r) > 0)
    assert (len(macro_economy.unemployment_r) > 0)
    assert (len(macro_economy.Q_GDP) > 0)
    assert (type(macro_economy.vix_index) == float)
    if true_vix_index is not None:
        assert (macro_economy.vix_index == true_vix_index)


def test_fetch_econ_row():
    conn = sqlite3.connect('test.db')
    cur = conn.cursor()
    cur.execute("DELETE FROM stockmarket_MacroEconomy;")
    rows = cur.execute("SELECT * FROM stockmarket_MacroEconomy;").fetchall()
    conn.commit()
    conn.close()
    first_row = fetch_the_latest_data("MacroEconomy", "test.db", "timestamp")
    time_diff = datetime.datetime.now() - datetime.datetime.strptime(first_row[0], "%Y-%m-%d %H:%M:%S.%f")
    two_minutes = datetime.timedelta(minutes=2)
    assert (time_diff < two_minutes)  # check whether new row is added into the table

    second_row = fetch_the_latest_data("MacroEconomy", "test.db", "timestamp")
    assert (first_row[0] == second_row[0])  # check whether minimum two hours update rule is obeyed




def test_add_new_stock_row():
    conn = sqlite3.connect("test.db")
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%stock';").fetchall()
    table = tables[0][0]
    stock = create_stock('Apple')
    stock.company_ticker = 'AAPL'
    row_id = add_stock_data_into_table(stock, "test.db")
    row = conn.execute("SELECT * FROM " + table + " WHERE ROWID = " + str(row_id) + ";").fetchone()
    print(row)
    assert (row != None)


def test_get_ticker():
    stock = CompanyStock("test")
    stock_ticker_dict = {"Facebook": "FB", "Alphabet": "GOOGL", "Tesla": "TSLA", "Amazon": "AMZN", "express": "AXP"}
    for key, value in stock_ticker_dict.items():
        tickers = stock.get_ticker(key)
        assert (value in tickers.values())


def test_catch_econ_api_error():
    # warning: to use this function you need to uncomment the second MacroEcon initiation in fet_latest_date function
    error_message = fetch_the_latest_data("MacroEconomy", "test.db")
    assert (type(error_message) == str)
    assert (error_message == "Too many requests! Please try a minute later")


def test_catch_stock_api_error():
    # test how my codes handle erros from API
    tickers_list = ["FB", "GOOGL", "TSLA", "AMZN", "JPM", "NFLX", "SAP"]
    count = 0
    for ticker in tickers_list:
        stock = CompanyStock("test", ticker)
        if type(stock.get_recent_financials()) == str:
            count += 1
    assert (count > 0)


def test_update_stock_data_and_retrieve():
    stock = create_stock("test", "GOOGL")
    row_id = add_stock_data_into_table(stock, "test.db")
    row_id = update_stock_data(row_id, "test.db")
    row = select_row(row_id, "stockmarket_stock", "test.db")
    stock_price = row[3]
    data_time_interval = row[7]
    assert type(stock_price) == list
    assert type(data_time_interval) == str


def test_get_axes():
    fed_rates = fetch_the_latest_data("MacroEconomy", "test.db", "fed_rate")[0]
    x_axis, y_axis, x_tick, interval = get_x_y_axis_data(fed_rates)
    assert len(x_axis) == len(y_axis)
    x_axis, y_axis, x_tick, interval = get_x_y_axis_data(fed_rates, "years")
    year_diff = datetime.datetime.now().year - 1954
    assert len(x_axis) == (year_diff + 1)


def test_fed_rate_predictor():
    econ = MacroEcon(empty_instance=True)
    econ_data = fetch_the_latest_data("MacroEconomy", "test.db")
    fed_rate = econ_data[2]
    inflation_rate = econ_data[4]
    monthly_fed = convert_data_by_given_interval(fed_rate)
    latest_data_date = datetime.datetime.strptime(fed_rate[0][0], "%Y-%m-%d")
    if latest_data_date.day != 1: monthly_fed = monthly_fed[1:]
    curr_inflation = econ.get_current_month_inflation()
    predictor = PredictHMM('fed_rate')
    result_tup = predictor.predict_fed_rate(monthly_fed, inflation_rate, curr_inflation)
    most_probable_state, interests, inflations, state_space, emission_space, model = result_tup
    print(f"HMM predicts the fed interest rate will be: {most_probable_state}")
    print(f"Initial Probabilities: {model.startprob_}")
    print(f"Transition Probabilities: {model.transmat_}")
    print(f"Emission Probabilities: {model.emissionprob_}")


def add_update_predictor_table(type: str, db_name:str = 'db.sqlite3'):
    # this function for testing the function in the stockmarket_predictor_database_function.py
    # this function uses the same codes as one in that file but with slight modification
    if type == 'fed_rate':
        # get the last data if there is any
        try:
            predictor_row = fetch_latest_predictor_data('fed_rate', db_name)
        except sqlite3.OperationalError:
            predictor_row = None
        if predictor_row is None or predictor_row[0] is None: prev_rowid = 0
        else: prev_rowid = int(predictor_row[0])
        # train the HMM model and get the results
        econ = MacroEcon(empty_instance=True)
        econ_data = fetch_the_latest_data("MacroEconomy", db_name)
        fed_rate = econ_data[2]
        inflation_rate = econ_data[4]
        monthly_fed = convert_data_by_given_interval(fed_rate)
        latest_data_date = datetime.datetime.strptime(fed_rate[0][0], "%Y-%m-%d")
        if latest_data_date.day != 1: monthly_fed = monthly_fed[1:]
        curr_inflation = econ.get_current_month_inflation()
        predictor = PredictHMM('fed_rate')
        result_tup = predictor.predict_fed_rate(monthly_fed, inflation_rate, curr_inflation)
        most_probable_state, interests, inflations, state_space, emission_space, model = result_tup
        initial_prob = convert_np_array_to_list(model.startprob_)
        assert(sum(initial_prob) - 1 < 0.001)
        transition_prob = convert_np_array_to_list(model.transmat_)
        emission_prob = convert_np_array_to_list(model.emissionprob_)

        # create a new predictor to be added to the database
        del predictor
        predictor = PredictHMM('fed_rate', initial_prob, transition_prob, emission_prob, state_space, emission_space)
        conn = sqlite3.connect(db_name)
        cur = conn.cursor()
        rowid = add_data_into_table(cur, "stockmarket_predictor", prev_rowid, predictor)
        conn.commit()
        conn.close()
        del predictor_row
        predictor_row = fetch_latest_predictor_data('fed_rate', db_name)
        print(f"Added predictor row: {predictor_row}")


def test_delete_rows():
    # warning this takes very long running time
    for i in range(5):
        add_update_predictor_table('fed_rate', 'test.db')
        delete_rows('stockmarket_predictor', 5, 'test.db', data_type='fed_rate')
    conn = sqlite3.connect('test.db')
    cur = conn.cursor()
    rows = cur.execute("SELECT * FROM stockmarket_predictor;").fetchall()
    assert (len(rows) == 5)



if __name__ == '__main__':
    # please use the the commented imports(the absolute imports) in stock_db_interact.py before running this file
    # create_test_db()  # this creats test case database. Uncomment for the first time test case running
    test_fetch_econ_row()
    test_add_new_stock_row()
    test_get_ticker()
    test_catch_stock_api_error()
    test_update_stock_data_and_retrieve()
    test_get_axes()
    # test_catch_econ_api_error()  # please see the function comment before running the function
    test_fed_rate_predictor()
    add_update_predictor_table('fed_rate', 'test.db')
    test_delete_rows()
