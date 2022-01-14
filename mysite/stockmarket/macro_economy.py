import time
import json

import mechanicalsoup
from urllib.request import urlopen
import re
import requests
import numpy as np
from scipy.stats import pearsonr
import datetime

from .operation_functions import *


class MacroEcon():
    def __init__(self, empty_instance=False):
        # empty_instance is used to create an instance without setting all the attributes at initialization
        
        # I'm sorry but I can't share my API key in public
        # you can get your free Alpha Vintage API key in https://polygon.io/stocks?gclid=Cj0KCQjw8p2MBhCiARIsADDUFVEHNFnLk6MIN7jCZR72_QWQF1W4UPqceq-fpOwUWTuGnDSGSYqO-K0aArp7EALw_wcB
        self.__Alpha_Vantage_key = your_api_key
        self.browser = mechanicalsoup.Browser()
        self.time = datetime.datetime.now()  # represents the time when the economy data was acquired from API
        if empty_instance is False:
            self.interest_rate = self.get_fed_interest_rate()
            self.longterm_treasury = self.get_treasury_yield()
            self.inflation_r = self.get_inflation_rate()  # expected change of inflation in next 12 months
            self.unemployment_r = self.get_unemployment_rate()
            self.Q_GDP = self.get_GDP()  # Quarterly GDP
        self.vix_index = self.get_vix()

    def get_current_month_inflation(self):
        # this method is preferred to be used for HMM to predict fed rate at next state(tomorrow)
        url = "https://www.usinflationcalculator.com/inflation/current-inflation-rates/"
        usinflationcalculator_page = self.browser.get(url)
        usinflationcalculator_html = usinflationcalculator_page.soup
        match = usinflationcalculator_html.find_all("div", {"class": "content-sidebar widget-area"})
        html_subset_str = match[0].prettify()
        start_index = html_subset_str.find("<u>") + 3
        end_index = html_subset_str[start_index:].find("</u>")
        end_index += start_index
        inflation_rate_str = html_subset_str[start_index:end_index].strip()
        inflation_rate_str = inflation_rate_str.replace("%", "")
        '''
        # this will be used if current web scraping codes are not working
        match = usinflationcalculator_html.find_all("div", {"class": "entry-content"})
        html_subset_str = match[0].prettify()
        #html_subset_str = match[0].text
        curr_month = self.time.month
        #html_subset_str.find("<strong>" + str(curr_month))
        month_str_int_converter = {"january": 1, "february": 2, "march": 3, "april":4, "may": 5, "june": 6, \
                                   "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12}
        start_index = 0
        for i in range(15 + curr_month - 1):
            start_index += html_subset_str[start_index:].find("<td")
            temp = start_index
            start_index += html_subset_str[start_index:].find(">")
        #table_cells = match.select("td")
        #start_index += html_subset_str[start_index:].find(">")
        end_index = start_index + html_subset_str[start_index:].find("<")
        print("debug: ", html_subset_str[start_index:end_index-1])
        curr_inflation = float(html_subset_str[start_index:end_index-1])
        '''
        curr_inflation = float(inflation_rate_str)
        return curr_inflation


    def get_vix(self):
        url = "https://www.google.com/finance/quote/VIX:INDEXCBOE"
        google_finance_vix_page = self.browser.get(url)
        vix_html = google_finance_vix_page.soup
        vix_html_str = vix_html.prettify()
        tag_index = vix_html_str.find('class="YMlKec fxKbKc"')
        start_index = tag_index + vix_html_str[tag_index:].find(">") + 1
        end_index = start_index + vix_html_str[start_index:].find("<")
        vix_index = ""
        for i in range(start_index, end_index):
            vix_index += vix_html_str[i]
        try:
            return float(vix_index)
        except ValueError:  # ValueError will be raised if there is no class="YMlKec fxKbKc" found
            return 0


    def get_fed_interest_rate(self, period="daily"):
        url = 'https://www.alphavantage.co/query?function=FEDERAL_FUNDS_RATE&interval=' + period \
              + '&apikey=' + self.__Alpha_Vantage_key
        r = requests.get(url)
        fed_data = r.json()
        fed_rates = [(elem['date'], elem['value']) for elem in fed_data['data']]
        return fed_rates


    def get_treasury_yield(self):
        url = 'https://www.alphavantage.co/query?function=TREASURY_YIELD&interval=daily&maturity=10year&apikey=' \
              + self.__Alpha_Vantage_key
        r = requests.get(url)
        lt_treasury_yield = r.json()
        treasury_yields = [(elem['date'], elem['value']) for elem in lt_treasury_yield['data']]
        return treasury_yields


    def get_inflation_rate(self):
        url = 'https://www.alphavantage.co/query?function=INFLATION_EXPECTATION&apikey=' + self.__Alpha_Vantage_key
        r = requests.get(url)
        inflation = r.json()
        inflation_rates = [(elem['date'], elem['value']) for elem in inflation['data']]
        return inflation_rates  # monthly interval


    def get_unemployment_rate(self):
        url = 'https://www.alphavantage.co/query?function=UNEMPLOYMENT&apikey=' + self.__Alpha_Vantage_key
        r = requests.get(url)
        unemployment_rate = r.json()
        rates = [(elem['date'], elem['value']) for elem in unemployment_rate['data']]
        return rates


    def get_GDP(self):
        url = 'https://www.alphavantage.co/query?function=REAL_GDP&interval=quarterly&apikey=' \
              + self.__Alpha_Vantage_key
        r = requests.get(url)
        quarterly_gdp = r.json()
        gdp_lst = []
        for i in range(len(quarterly_gdp['data']) - 1):
            current_quarter_date = quarterly_gdp['data'][i]['date']
            this_quarter = float(quarterly_gdp['data'][i]['value'])
            last_quarter = float(quarterly_gdp['data'][i+1]['value'])
            quarterly_gdp_growth = round(100 * (this_quarter - last_quarter) / last_quarter, 2)
            gdp_lst.append((current_quarter_date, quarterly_gdp_growth))
        return gdp_lst


    def how_corrleated(self, variable_x, variable_y):
        corr, _ = pearsonr(variable_x, variable_y)
        print(f"Pearson Correlation: {corr}")

if __name__ == '__main__':
    macro_economy = MacroEcon()
