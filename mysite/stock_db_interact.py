'''
This python script is used for stock app to get from or add data directly to database
'''

from datetime import datetime, timedelta
from copy import deepcopy
import json

import sqlite3

# use the commented imports(the absolute imports) when running test.py
'''
from mysite.stockmarket.macro_economy import *
from mysite.stockmarket.CompanyStock import *
from mysite.stockmarket.operation_functions import convert_to_json, convert_to_list
'''
from stockmarket.macro_economy import *
from stockmarket.CompanyStock import *
from stockmarket.operation_functions import convert_to_json, convert_to_list



def add_data_into_table(cursor, table_name, rowid, data):
    # data expects either instance of MacroEcon or CompanyStock
    # cursor is the sqlite3 cursor
    # table_name is the name of the table where the new data will be added
    # rowid is the id of the row one before the soon-to-be newly added one
    # returns rowid of the newly added data
    if table_name == "stockmarket_macroeconomy":
        macro_econ = data
        rowid += 1
        tup_json = (rowid,
                    convert_to_json(str(macro_econ.time)),
                    convert_to_json(macro_econ.interest_rate),
                    convert_to_json(macro_econ.longterm_treasury),
                    convert_to_json(macro_econ.inflation_r),
                    convert_to_json(macro_econ.unemployment_r),
                    convert_to_json(macro_econ.Q_GDP),
                    convert_to_json(macro_econ.vix_index)  # remove this if not working
                    )

        cursor.execute("INSERT INTO " + table_name + " VALUES (?, ?, ?, ?, ?, ?, ?, ?);", tup_json)
    elif table_name == "stockmarket_predictor":
        predictor = data
        rowid += 1
        curr_time = datetime.datetime.strftime(datetime.datetime.now(), "%Y-%m-%d %H:%M:%S")
        tup_json = (rowid,
                    convert_to_json(predictor.type),
                    convert_to_json(curr_time),
                    convert_to_json(predictor.initial),
                    convert_to_json(predictor.transition),
                    convert_to_json(predictor.emission),
                    convert_to_json(predictor.state_space),
                    convert_to_json(predictor.emission_space)
        )
        cursor.execute("INSERT INTO " + table_name + " VALUES (?, ?, ?, ?, ?, ?, ?, ?);", tup_json)
    else:
        stock = data
        rowid += 1
        tup_json = (rowid,
                    convert_to_json(stock.company_name),
                    convert_to_json(stock.company_ticker),
                    convert_to_json(stock.stock_price),
                    convert_to_json(stock.dividends),
                    convert_to_json(stock.volume),
                    convert_to_json(stock.stock_splits),
                    convert_to_json(stock.interval),
                    convert_to_json(stock.financials)
        )
        cursor.execute("INSERT INTO " + table_name + " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);", tup_json)
    return rowid


def select_row(rowid: int, table_name: str, db_name: str ='db.sqlite3', *fields):
    # return a row at given row id in given table
    conn = sqlite3.connect(db_name)
    if len(fields) == 1 and type(fields[0]) == tuple:
        # this will be True only when this functions is called by fetch_latest_data function
        fields = fields[0]
    if len(fields) > 0:
        query_fields_str = ""
        for i in range(len(fields)):
            query_fields_str += fields[i]
            if i < (len(fields) - 1): query_fields_str += ", "
        row = conn.execute("SELECT " + query_fields_str + " FROM " + table_name + \
                           " WHERE ROWID = " + str(rowid) + ";").fetchone()
    else:
        row = conn.execute("SELECT *  FROM " + table_name + " WHERE ROWID = " + str(rowid) + ";").fetchone()
    conn.commit()
    conn.close()
    return decode_json_in_row(row)


def decode_json_in_row(row):
    new_row = [convert_to_list(row[0]) if type(row[0]) == str else str(row[0])]
    for i in range(1, len(row)):
        elem = convert_to_list(row[i])
        new_row.append(elem)
    return new_row


def create_stock(company_name, ticker=None):
    new_stock_data = CompanyStock(company_name, ticker)
    return new_stock_data


def find_ticker(stock, company_name=None):
    # stock is class CompanyStock
    if company_name is None: company_name = stock.company_name
    stock.company_ticker = stock.get_ticker(company_name)
    return stock.company_ticker  # return data type: dictionary


def add_stock_data_into_table(stock, db_name:str = 'db.sqlite3'):
    # stock is class CompanyStock
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()
    prev_id = cur.execute("SELECT MAX(ROWID) FROM stockmarket_stock;").fetchone()[0]
    prev_id = 0 if prev_id is None else int(prev_id)
    row_id = add_data_into_table(cur, "stockmarket_stock", prev_id, stock)
    conn.commit()
    conn.close()
    return row_id


def update_stock_data(stock_rowid: int, db_name: str = 'db.sqlite3'):
     conn = sqlite3.connect(db_name)
     rowid_str = str(stock_rowid)
     row = conn.execute("SELECT * FROM stockmarket_stock WHERE ROWID=?", (rowid_str,)).fetchone()
     row = decode_json_in_row(row)
     stock = CompanyStock(row[1], row[2])
     stockprice_error = stock.get_stock_history()
     stock.get_recent_financials()
     if stockprice_error is not None:
         return stockprice_error
     tup_json = (
         convert_to_json(stock.stock_price),
         convert_to_json(stock.stock_splits),
         convert_to_json(stock.volume),
         convert_to_json(stock.dividends),
         convert_to_json(stock.interval),
         convert_to_json(stock.financials),
         rowid_str
     )
     conn.execute("UPDATE stockmarket_stock SET stock_price = ?, dividends = ?, \
                   volume = ?, stock_splits = ?, interval = ?, financials = ? \
                   WHERE ROWID = ?;", tup_json)
     conn.commit()
     conn.close()
     return stock_rowid


def delete_rows(table_name, num_rows_kept: int, db_name: str = 'db.sqlite3', data_type=None):
    # delete the old rows to limit the size of the table
    # Param: num_rows_kept = number of rows to be remained in data base. all the other rows will be deleted
    # Param: data_type = type of data in a table. mostly used for Predictor table
    # return nothing
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()
    rows = conn.execute("SELECT * FROM " + table_name + " ORDER BY timestamp DESC;").fetchall()

    type_json = convert_to_json(data_type) if data_type is not None else None
    # delete all the rows which are not the most recent given number of rows
    count = 0
    for i in range(0, len(rows)):
        if data_type is not None and rows[i][1] == type_json:
            count += 1
        else:
            count += 1
        if count > num_rows_kept:
            delete_cmd = "DELETE FROM " + table_name + " WHERE ROWID = " + str(i)
            cur.execute(delete_cmd + ";")

    conn.commit()
    conn.close()


def fetch_the_latest_data(data_type: str, db_name: str = 'db.sqlite3', *fields):
    # data_type(class) is data to be retrieved; either MacroEconomy or Stock data
    # field to be retrieved. Must match with one of the fields name of the data_type
    # return the most recently updated field of the data type
    table_name = "stockmarket_macroeconomy" if data_type == "MacroEconomy" else "stockmarket_stock"
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()

    if data_type == "MacroEconomy":
        curr_time = datetime.datetime.now()
        time_str = curr_time.strftime("%Y-%m-%d %H:%M:%S.%f")

        # if there was no data in DB, row = (None, None)
        row = cur.execute("SELECT ROWID, MAX(timestamp) FROM " + table_name + ";").fetchone()
        data_date_str = convert_to_list(row[1]) if row[1] is not None else row[1]
        prev_id = int(row[0]) if row[0] is not None else 0
        is_update_needed = False
        if data_date_str is not None:
            # at least two hours are required to get new market data to avoid submitting too many requests to API
            data_date = datetime.datetime.strptime(data_date_str, "%Y-%m-%d %H:%M:%S.%f")
            delta_time = curr_time - data_date
            print(f"time difference: {delta_time}")
            two_hour_window = datetime.timedelta(hours=2)
            if delta_time >= two_hour_window: is_update_needed = True
        else: is_update_needed = True
        if is_update_needed:
            try:
                econ_data = MacroEcon()
            except KeyError:  # key error will occur when API receives too many requests in one minute
                return "Too many requests! Please try a minute later"  # error message
            row_id = add_data_into_table(cur, table_name, prev_id, econ_data)
        else:
            row_id = prev_id

    conn.commit()
    conn.close()
    row = select_row(row_id, table_name, db_name, fields)
    return row


def fetch_latest_predictor_data(predictor_type: str, db_name:str = 'db.sqlite3'):
    conn = sqlite3.connect(db_name)
    type_json = convert_to_json(predictor_type)
    select_cmd = "SELECT ROWID, MAX(timestamp) FROM stockmarket_predictor" + " WHERE type = '" + type_json + "';"
    cur = conn.execute("SELECT * FROM stockmarket_predictor;")
    # cur.description
    temp_row = conn.execute(select_cmd).fetchone()
    if temp_row[0] is not None:
        rowid = temp_row[0]
        row = select_row(rowid, "stockmarket_predictor", db_name=db_name)
    else:
        row = temp_row

    conn.commit()
    conn.close()
    return row
