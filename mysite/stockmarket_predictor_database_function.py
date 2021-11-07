# This is specifically designated for adding or updating data in predictor table at backend
# Users should not have access to any function in here
# updating and adding data for predictor is preferred here because running the training HMM may overload cache
from stock_db_interact import *
from stockmarket.operation_functions import *
from stockmarket.stockmarket_predictor import *


def add_update_predictor_table(type: str, db_name:str = 'db.sqlite3'):
    # At least one MacroEconomy data is required to be in the database to run this function
    # Param: type is the predictor type
    # return nothing
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
        econ_data = fetch_the_latest_data("MacroEconomy")
        fed_rate = econ_data[2]
        inflation_rate = econ_data[4]
        monthly_fed = convert_data_by_given_interval(fed_rate)
        latest_data_date = datetime.datetime.strptime(fed_rate[0][0], "%Y-%m-%d")
        if latest_data_date.day != 1: monthly_fed = monthly_fed[1:]
        curr_inflation = econ.get_current_month_inflation()
        predictor = PredictHMM('fed_rate')
        result_tup = predictor.predict_fed_rate(monthly_fed, inflation_rate, curr_inflation)
        most_probable_state, interests, inflations, state_space, emission_space, model = result_tup
        # convert np array to 2d list
        initial_prob = convert_np_array_to_list(model.startprob_)
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
        print("New Predictor Row Is Added")


if __name__ == '__main__':
    add_update_predictor_table('fed_rate', db_name="stockmarket/stockmarket_db.sqlite3")
    delete_rows('stockmarket_predictor', 5, data_type='fed_rate', db_name="stockmarket/stockmarket_db.sqlite3")
