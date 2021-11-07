import json
import datetime
import io, base64

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use('Agg')
plt.rcParams['axes.facecolor'] = 'black'
plt.rcParams['axes.xmargin'] = 0


def is_first_day_of_interval(interval, date_ymd):
    if interval == "months":
        if date_ymd.day == 1: return True
        else: return False
    if interval == "quarters":
        if date_ymd.month in (1, 4, 7, 10) and date_ymd.day == 1: return True
        else: return False
    if interval == "years":
        if date_ymd.month == 1 and date_ymd.day == 1: return True
        else: return False
    if interval == "10yrs":
        if date_ymd.year % 10 == 0 and date_ymd.day == 1: return True
        else: return False


def date_str_format(time_interval="months"):
    if time_interval == "days": return "%Y-%m-%d"
    if time_interval == "years": return "%Y"
    else: return "%Y-%m"


def convert_to_json(*args):
    if len(args) == 1: args = args[0]
    data_json = json.dumps(args)
    return data_json


def convert_to_list(json_str):
    # decode the json to its original type
    # convert json to list of dict(key: date, value: value) if the original type is dict(rarely happens)
    data_decoded = json.loads(json_str)
    if type(data_decoded) == dict:
        data_list = [{'date': key, 'value': value} for key, value in data_decoded.items()]
        return data_list
    return data_decoded  # decoded data is already in the type we want


def convert_dictionary(lambda_f, *maps):
    # maps are expected to be one to many dictionaries
    # lambda_f is a function that returns computed value in an inside list
    # return a list of tuples or a tuple(if only one key value pair in dictionary)
    result_list = []
    first_dict = maps[0]
    for key, value in first_dict.items():
        if len(maps) > 1:
            values = []
            for i in range(len(maps)):
                values.append(maps[i][key])
        else: values = value
        if type(key) not in (int, float, str):
            key = str(key)
        result_list.append((key, lambda_f(values)))
    result_list.sort(key=lambda elem: elem[0], reverse=True)
    return result_list


def convert_np_array_to_list(np_array):
    # np_array is expected to be 2d array
    # return 2d list
    result_list = []
    for elem in np_array:
        if type(elem) == np.ndarray: result_list.append([inner_elem for inner_elem in elem])
        else: result_list.append(elem)
    return result_list


def convert_data_by_given_interval(data_container, time_interval="months"):
    data_by_new_interval = []
    count = 0
    total = 0
    for i in range(len(data_container)):
        day_str = data_container[i][0]
        date_ymd = datetime.datetime.strptime(day_str, "%Y-%m-%d")
        try:
            total += float(data_container[i][1])
        except ValueError:
            total += 0
        count += 1
        if is_first_day_of_interval(time_interval, date_ymd):
            avg_values = total / count
            count = 0
            total = 0
            data_by_new_interval.append((day_str, avg_values))
    if count > 0:
        avg_values = total / count
        data_by_new_interval.append((day_str, avg_values))
    return data_by_new_interval


def get_x_y_axis_data(values_container, time_interval="months", override = False):
    # override is a parameter that forces to produce the full history of data rather than recent 5 years data
    period = len(values_container) if time_interval == "years" or override else 5 * 365 + 1
    total_y_values = 0
    count = 0
    days, y_axis, x_tick = None, None, None
    beg_period_date = datetime.datetime.strptime(values_container[period-1][0], "%Y-%m-%d")
    beg_period_date = datetime.datetime.strftime(beg_period_date, date_str_format(time_interval))
    end_period_date = datetime.datetime.strptime(values_container[0][0], "%Y-%m-%d")
    end_period_date = datetime.datetime.strftime(end_period_date, date_str_format(time_interval))

    for i in range(period):
        date_ymd = datetime.datetime.strptime(values_container[i][0], "%Y-%m-%d")
        day_str = datetime.datetime.strftime(date_ymd, date_str_format(time_interval))
        try:
            y_float = float(values_container[i][1])
        except ValueError:
            y_float = 0
        total_y_values += y_float
        count += 1
        if is_first_day_of_interval(time_interval, date_ymd):
            avg_values = total_y_values / count
            count = 0
            total_y_values = 0
            if days is None:
                x_tick = [end_period_date]
                y_axis = [avg_values]
                days = [end_period_date]
            else:
                y_axis.append(avg_values)
                days.append(day_str)
                # to minimize the number of ticks on the x axis
                tickmark_interval = "10yrs" if time_interval == "years" else "years"
                if is_first_day_of_interval(tickmark_interval, date_ymd): x_tick.append(day_str)
                elif i == period - 1: x_tick.append(beg_period_date)
    if count > 0:
        avg_values = total_y_values / count
        x_tick.append(beg_period_date)
        y_axis = np.append(y_axis, avg_values)
        days = np.append(days, beg_period_date)
    days = np.flip(days)
    y_axis = np.flip(y_axis)
    x_tick = np.flip(x_tick)
    return days, y_axis, x_tick, time_interval


class GraphTool():
    def __init__(self):
        self.fig = plt.figure(figsize=(12, 12), facecolor='black')
        self.ax = self.fig.add_subplot(111)
        plt.tick_params(colors='white', which='both')
        self.ax.tick_params(axis='x', rotation=40, labelsize=7)
        self.ax.grid(linestyle="--", linewidth=0.5, color='.25', zorder=-10)
        self.graph_img = None

    def graph_with_one_y(self, days, y_values, x_tick, graph_title: str, x_label: str,
               y_label, y_tick_interval=0.25):
        self.ax.plot(days, y_values, 'green', marker='.', markersize=4)
        # setting ticks and adjusting ticks formatting
        self.ax.set_xticks(x_tick)
        min_end = -0.25 if -0.25 < y_values.min() else y_values.min()
        y_ticks = np.append(np.arange(min_end, 0, y_tick_interval),
                            np.arange(0, y_values.max() + y_tick_interval, y_tick_interval))
        self.ax.set_yticks(y_ticks)

        # setting title and labels and changing formatting of those
        self.ax.set_title(graph_title, fontsize=15, color='blue', fontweight='bold')
        self.ax.set_xlabel(x_label)
        self.ax.set_ylabel(y_label)
        self.ax.xaxis.label.set_color("white")
        self.ax.yaxis.label.set_color("white")

        # adding a grid in the graph and reducing the paddings around the figure
        self.ax.grid(linestyle="--", linewidth=0.5, color='.25', zorder=-10)
        plt.tight_layout()

        flike = io.BytesIO()
        self.fig.savefig(flike)
        b64_image = base64.b64encode(flike.getvalue()).decode()
        self.graph_img = b64_image
        return b64_image


    def graph_with_two_y(self, days, x_tick, graph_title: str, x_label: str,
               y_labels, y_ticks, *y_data_sets):
        # Param: days and x_tick are expected to be numpy array or list
        # Param: y_labels and y_ticks are tuples
        # Param: y_values_containers(tuple of numpy array or list) will not be expected to contain more than two arrays
        y_values_set1, y_values_set2 = y_data_sets
        y_label1, y_label2 = y_labels
        y_tick1, y_tick2 = y_ticks

        # plot the first y data set
        self.ax.set_title(graph_title, fontsize=15, color='blue', fontweight='bold')
        self.ax.set_xlabel(x_label)
        self.ax.xaxis.label.set_color("white")
        self.ax.set_ylabel(y_label1, color='green')
        self.ax.plot(days[:-1], y_values_set1[:-1], color='green')
        # the predicted data is plotted with blue asterisk point
        self.ax.plot(days[-1], y_values_set1[-1], marker="o", markersize=11, color='blue')
        self.ax.set_xticks(x_tick)
        self.ax.tick_params(axis='y', labelcolor='green')

        # plot the second y data set
        ax2 = self.ax.twinx()
        ax2.set_ylabel(y_label2, color='yellow')
        ax2.plot(y_values_set2, color='yellow')
        ax2.tick_params(axis='y', labelcolor='yellow')

        # set y ticks for both axes
        self.ax.set_yticks(y_tick1)
        ax2.set_yticks(y_tick2)

        # adding a grid in the graph and reducing the paddings around the figure
        self.ax.grid(linestyle="--", linewidth=0.5, color='.25', zorder=-10)
        plt.tight_layout()

        flike = io.BytesIO()
        self.fig.savefig(flike)
        b64_image = base64.b64encode(flike.getvalue()).decode()
        self.graph_img = b64_image
        return b64_image

