# Welcome to Alpha Vantage! Your dedicated access key is: SVVM4XB84BCI15YH.
from collections import OrderedDict

import yfinance
import requests
from yahooquery import Ticker
import numpy as np
import mechanicalsoup

from .operation_functions import *


class CompanyStock():
    def __init__(self, company_name, ticker=None, *args):
        self.company_name = company_name
        self.company_ticker = ticker
        self.stock_price = args[0] if (args is not None and len(args) > 0) else None
        self.dividends = args[1] if (args is not None and len(args) > 1) else None
        self.volume = args[2] if (args is not None and len(args) > 2) else None
        self.stock_splits = args[3] if (args is not None and len(args) > 3) else None
        self.interval = args[4] if (args is not None and len(args) > 4) else None
        self.financials = args[5] if (args is not None and len(args) > 5) else None
        self._Alpha_Vantage_key = "SVVM4XB84BCI15YH"
        self.__polygon_io_key = "U6vW1exaN05RpORkVBISba_g6cxFcnuV"

        self.stock_data = None

    def __str__(self):
        return self.company_name + "'s " + str(self.company_ticker) + " : " + str(self.stock_price)

    def set_company_ticker(self, ticker):
        self.company_ticker = ticker

    def get_ticker(self, company_name: str):
        # return all the tickers(dict) which are related to the name of the company in json
        # maybe use the returned json to display the buttons of the full legal company stock names with value equal to ticker
        url = "https://api.polygon.io/v3/reference/tickers?market=stocks&search=" + company_name + \
              "&active=true&sort=ticker&order=asc&limit=10&apiKey=U6vW1exaN05RpORkVBISba_g6cxFcnuV"
        r = requests.get(url)
        tickers_json = r.json()
        tickers = {}
        try:
            for ticker in tickers_json['results']:
                tickers[ticker['name']] = ticker['ticker']
        except KeyError:  # key error will occur when API receives too many requests in one minute
            return "Too many requests! Please try a minute later"  # error message
        return tickers

    def get_recent_financials(self):
        ticker = self.company_ticker
        url = "https://api.polygon.io/vX/reference/financials?ticker=" + ticker\
              + "&include_sources=true&apiKey=" + self.__polygon_io_key
        r = requests.get(url)
        try:
            financials = r.json()['results'][0]
            income_statement = financials['financials']['income_statement']
            balance_sheet = financials['financials']['balance_sheet']
            financials_items = {
                'Net Income': 'net_income_loss',
                'Earnings Per Share': 'basic_earnings_per_share',
                'Total Assets': 'assets',
                'Total Liabilities': 'liabilities',
                'Total Equity': 'equity'
            }
            self.financials = []  # nested list, where second element of inner list is a tuple(value, unit)
            for account_name, api_key in financials_items.items():
                if account_name in ('Net Income', 'Earnings Per Share'):
                   account_balance = (income_statement[api_key]['value'], income_statement[api_key]['unit'])
                else:
                    account_balance = (balance_sheet[api_key]['value'], balance_sheet[api_key]['unit'])
                self.financials.append([account_name, account_balance])
            fianacial_period = (financials['fiscal_year'] + " " + financials['fiscal_period'])
            self.financials.append(['Fiscal Period', fianacial_period])
            date_period = financials['start_date'] + " - " + financials['end_date']
            self.financials.append(['Date Period', date_period])
        except IndexError:  # index error will occur when financials for the request company is not available in API
            self.financials = "I'm sorry. Financials for this company are not available in this application yet"
        except KeyError:  # key error will occur when API receives too many requests in one minute
            self.financials = "Too many requests! Please try a minute later"
        return self.financials

    def get_stock_data(self):
        stock = Ticker(self.company_ticker)
        stock_data = stock.summary_detail
        try:
            key = list(stock_data.keys())[0]
            stock = stock_data[key]
        except KeyError:  # API doesn't support this stock
            return "I'm sorry we don't have data for the requested stock"
        try:
            self.stock_data = OrderedDict()
            self.stock_data['Average Price'] = (stock['open'] + stock['previousClose']) /2
            self.stock_data['Volume'] = stock['volume']
            self.stock_data['Market Cap'] = stock['marketCap']
            self.stock_data['Currency'] = stock['currency']
            if stock.get('exDividendDate'):
                self.stock_data['Ex Dividend Date'] = stock['exDividendDate']
            if stock.get('dividendYield'):
                self.stock_data['Dividend Yield'] = stock['dividendYield']
            if stock.get('dividendRate'):
                self.stock_data['Dividend Rate'] = stock['dividendRate']
        except KeyError: # API request issue
            return "Too many requests! Please try a minute later"  # error message


    # since yfinance(API) has some issue, this function is currently not being used until the API is back again
    def get_stock_history(self, period: str = "1y", interval: str ="1d"):
        # period = one of (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
        # interval cannot exceed 60 days. interval in (1m, 2m, 5m, 15m, 30m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)
        # nothing will be returned unless error is raised
        stock_history = yfinance.Ticker(self.company_ticker).history(period=period, interval=interval)

        # key: 'Open', 'High', 'Low', 'Close', 'Volume', 'Dividends', 'Stock Splits'. value(dict): {timestamp: value}
        stock_history_dict = stock_history.to_dict()
        print(stock_history_dict)
        try:
            self.stock_price = convert_dictionary(lambda values: sum(values)/len(values),
                                     stock_history_dict['Open'], stock_history_dict['Close'])
            self.volume = convert_dictionary(lambda value: value, stock_history_dict['Volume'])
            self.dividends = convert_dictionary(lambda value: value, stock_history_dict["Dividends"])
            self.stock_splits = convert_dictionary(lambda value: value, stock_history_dict["Stock Splits"])
            self.interval = interval
            print(self.stock_splits)
        except KeyError:  # key error will occur when API receives too many requests in one minute
            return "Too many requests! Please try a minute later"  # error message


if __name__ == '__main__':
    app = CompanyStock()
    app.set_company_ticker("AAPL")
    app.get_stock_history("1y")
    app.get_recent_financials(app.company_ticker)
    print(app.volume)