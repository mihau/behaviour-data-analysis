#!/usr/bin/env python
import csv
import xlwt
import time
import datetime
from dateutil import parser
import xlsxwriter
import os
from pprint import pprint
import traceback
from collections import defaultdict
import numpy as np
import click

import pandas as pd

SUBDIR = "NOR 3 05"
PICKER = 2
DATA_FOLDER = "/Users/mszymans/private_dev/mice_datasets/"
OUTPUT_SUMMARY_FOLDER = "/Users/mszymans/private_dev/summaries/"
SOURCE_FILES_FOLDER = [DATA_FOLDER+ "NOR day 0/", DATA_FOLDER+ 'NOR 3 05/', DATA_FOLDER + 'NOR 9.05 complete/'][PICKER]
OUTPUT_FILE = [OUTPUT_SUMMARY_FOLDER + 'nor_day_0_processed.xlsx', OUTPUT_SUMMARY_FOLDER + 'NOR_3_05_processed.xlsx', OUTPUT_SUMMARY_FOLDER + 'NOR_9_05.xlsx'][PICKER]
OUTPUT_DIRECTORY = [DATA_FOLDER + 'nor_day_0_fixed/', DATA_FOLDER + 'nor_3_05_fixed/', DATA_FOLDER + 'nor_9_05_fixed/'][PICKER]
ADDITIONAL_FILES = [DATA_FOLDER + 'NOR dzien 0 dodatkowe/', DATA_FOLDER + 'NOR 3 05 dodatkowe/', DATA_FOLDER + 'NOR 9 05 dodatkowe/']

def convert_time(t):
    return datetime.datetime.fromtimestamp(float(t)/1000000.0)

def convert_time_new(t):
    ''' Converting timestamps to timedeltas '''
    return datetime.datetime.fromtimestamp(float(t)/1000000.0) - datetime.datetime.fromtimestamp(0.0)

def dump_time(t):
    return t.total_seconds()

LABEL_MAP = {
    'compensated_duration': {
        'label': 'compensated_duration',
        'formatter': convert_time
    },
    'compensated_end_time': {
        'label': 'compensated_end_time',
        'formatter': convert_time
    },
    'compensated_event_duration_sum': {
        'label': 'compensated_event_duration_sum',
        'formatter': convert_time
    },
    'compensated_object_duration_sum': {
        'label': 'compensated_object_duration_sum',
        'formatter': convert_time
    },
    'compensated_relative_end_time': {
        'label': 'compensated_relative_end_time',
        'formatter': convert_time
    },
    'duration': {
        'label': 'duration',
        'formatter': convert_time

    },
    'duration_overflow': {
        'label': 'duration_overflow',
        'formatter': convert_time
    },
    'duration_sum': {
        'label': 'duration_sum',
        'formatter': convert_time
    },
    'end_time': {
        'label': 'end_time',
        'formatter': convert_time
    },
    'object_duration_sum': {
        'label': 'object_duration_sum',
        'formatter': convert_time
    },
    'object_id': {
        'label': 'object_id',
    },
    'relative_end_time': {
        'label': 'relative_end_time',
        'formatter': convert_time
    },
    'relative_start_time': {
        'label': 'relative_start_time',
        'formatter': convert_time

    },
    'start_time': {
        'label': 'start_time',
        'formatter': convert_time
    },
    'final_event_of': {
        'label': 'final_event_of',
    }
}


def start():
    files_to_process = os.listdir(SOURCE_FILES_FOLDER)[:]
    workbook = xlsxwriter.Workbook(OUTPUT_FILE)
    header = workbook.add_format({'bold': True, 'border': True})

    # class ExplorationEvent(object):
    #     def __init__(self):


    summary_worksheet = workbook.add_worksheet("summary")
    summary_worksheet.set_column('A:A', 30.0)
    summary_worksheet.set_column('B:D', 22.0)

    for indx, label in enumerate(['filename', 'object 1 exploration time', 'object 2 exploration time', 'time to reach 20s']):
        summary_worksheet.write_string(0, indx, label, header)

def load_data(input_file):
    """ loads data from a csv file do a pandas DataFrame """
    data = pd.read_csv(
        input_file,
        sep=',',
        parse_dates=[0, 1, 2, 3, 4, 5, 6, 8, 9, 10, 11, 12, 13],
        date_parser=convert_time_new,
    )

    return data

def verify_data(data, duration_limit=datetime.timedelta(seconds=20)):
    """ verify data integrity assuming that only start time and end time of events are correct """
    start_event = data.ix[0]
    experiment_start_time = start_event.start_time

    # get the ids of objects appearing in the data
    object_ids = set(data.object_id.values)  # get the ids of objects
    object_ids.remove(0)  # excluding 0, which stands for start event

    # defined below are cumulative variables
    duration_sum = datetime.timedelta(seconds=0)
    object_duration_sums = defaultdict(datetime.timedelta)


    for indx, event in data.iterrows():
        # increase the cumulative variables
        duration_sum += event.end_time - event.start_time
        object_duration_sums[event.object_id] += event.end_time - event.start_time

        # check if end time is later or same as start time
        assert event.end_time >= event.start_time
        # check if the relative start time is correct
        assert event.relative_start_time == event.start_time - experiment_start_time
        # check if the relative end time is correct
        assert event.relative_end_time == event.end_time - experiment_start_time
        # check if event duration is the difference between the end time and start time
        assert event.end_time - event.start_time == event.duration
        # check if duration sum is the sum of all events that have been recorded so far, including the current one
        assert event.duration_sum == duration_sum
        # check if object duration sum is equal to the sum of durations of events related to the object with a particular id
        assert event.object_duration_sum == object_duration_sums[event.object_id]
        # check if duration overflow is the amount of time for which the event exceeded the duration limit (sepcific to the experiment)
        assert event.duration_overflow == float(np.heaviside((event.duration_sum - duration_limit).total_seconds(), 0)) * (event.duration_sum - duration_limit)
        # check if compensated duration is the duration sum minus the duration overflow
        # TODO: figure out how skewed are the results
        assert event.compensated_duration == event.duration - event.duration_overflow
        # check if compensated end time is the end time minus the duration_overflow
        if indx != 0:
            assert event.compensated_end_time == event.end_time - event.duration_overflow
        # check if compensated relative end time is the relative end time minus the duration overflow
        assert event.compensated_relative_end_time == event.relative_end_time - event.duration_overflow
        # check if compensated event duration sum is the event duration sum minus the duration overflow
        assert event.compensated_event_duration_sum == event.duration_sum - event.duration_overflow
        # check if compensated object duration sum is the object duration sum minus the duration overfow
        assert event.compensated_object_duration_sum == event.object_duration_sum - event.duration_overflow

    # cumulative values assertions
    # TODO: allow for this to fail
    # assert duration_sum >= duration_limit


def fix_data(data, input_filename, duration_limit=datetime.timedelta(seconds=20)):
    additional_filename = (ADDITIONAL_FILES[PICKER] + input_filename)[:-4] + '_dodatkowy.csv'
    if os.path.isfile(additional_filename):
        additional_data = load_data(additional_filename)
        data = data.append(additional_data[1:], ignore_index=True)


    start_event = data.ix[0]
    experiment_start_time = start_event.start_time

    # get the ids of objects appearing in the data
    object_ids = set(data.object_id.values)  # get the ids of objects
    object_ids.remove(0)  # excluding 0, which stands for start event

    # defined below are cumulative variables
    duration_sum = datetime.timedelta(seconds=0)
    object_duration_sums = defaultdict(datetime.timedelta)

    for indx, event in data.iterrows():
        duration_sum += event.end_time - event.start_time
        object_duration_sums[event.object_id] += event.end_time - event.start_time

        data.at[indx, 'relative_start_time'] = event.start_time - experiment_start_time
        data.at[indx, 'relative_end_time'] = event.end_time - experiment_start_time
        data.at[indx, 'duration'] = event.end_time - event.start_time
        data.at[indx, 'duration_sum'] = duration_sum
        data.at[indx, 'object_duration_sum'] = object_duration_sums[event.object_id]
        data.at[indx, 'duration_overflow'] = pd.to_timedelta(float(np.heaviside((duration_sum - duration_limit).total_seconds(), 0.0)) * (duration_sum - duration_limit))
        data.at[indx, 'compensated_duration'] = pd.to_timedelta(data.at[indx, 'duration'] - data.at[indx, 'duration_overflow'])
        if indx != 0:
            data.at[indx, 'compensated_end_time'] = event.end_time - data.at[indx, 'duration_overflow']
        data.at[indx, 'compensated_relative_end_time'] = data.at[indx, 'relative_end_time'] - data.at[indx, 'duration_overflow']
        data.at[indx, 'compensated_event_duration_sum'] = data.at[indx, 'duration_sum'] - data.at[indx, 'duration_overflow']
        data.at[indx, 'compensated_object_duration_sum'] = data.at[indx, 'object_duration_sum'] - data.at[indx, 'duration_overflow']

    return data


def process_data_file(input_file, workbook, summary_worksheet, file_indx, time_limit, header_format):
    TIME_LIMIT = time_limit
    reader = csv.reader(input_file, delimiter=',')
    data = []
    for idx, row in enumerate(reader):
        if idx == 0:
            labels = row
        else:
            data.append(row)
    # workbook = xlwt.Workbook()
    worksheet_name = ''.join(os.path.basename(input_file.name).split('.')[0:2])
    worksheet = workbook.add_worksheet(worksheet_name)
    worksheet.set_column('A:R', 16.0)

    #style = xlwt.XFStyle()
    #style.num_format_str = "mm:ss.0"
    date_format = workbook.add_format({'num_format': 'mm:ss.000', 'align': 'left'})

    data.sort(key=lambda x: (int(x[7]), int(x[0]))) # sort by object id then by time

    def mark_last_event(d, object_id):
        # print(object_events)
        found_candidate = None
        found = 0
        overflow = False
        for indx, row in enumerate(d):
            if row[7] == str(object_id):
                # print(row[12])
                if int(row[12]) == TIME_LIMIT*1000000 and not found:
                    row.append(object_id)
                    overflow = True
                    found = indx
                else:
                    found_candidate = indx
                    row.append(0)
                #row[14] = 0
        if not found:
            found = found_candidate
            data[found_candidate][14] = object_id
        return found, overflow

    labels.append('final_event_of')
    f1, o1 = mark_last_event(data, 1)
    # f2, o2 = mark_last_event(data, 2)
    # # print(f1, f2)
    last_event = f1
    # last_event = None
    # if int(data[f1][2]) > int(data[f2][2]):
    #     if o1 and o2:
    #         data[f1-1][14] = 1
    #         data[f1][14] = 0
    #         f1 = f1 - 1
    #     last_event = f1
    # else:
    #     if o1 and o2:
    #         data[f2-1][14] = 2
    #         data[f2][14] = 0
    #         f2 = f2 - 1
    #     last_event = f2
    # if int(data[f1][2]) > int(data[f2][2]):
    #     last_event = f1
    # else:
    #     last_event = f2

    # set labels on top of the files
    for indx, label in enumerate(labels):
        worksheet.write_string(0, indx, LABEL_MAP.get(label).get('label'), header_format)

    for row_indx, row in enumerate(data):
        # assert int(row[1]) - int(row[0]) == int(row[4])  # check if duration is ok
        # assert int(row[4]) - int(row[])
        for cell_indx, cell in enumerate(row):
            formatter = LABEL_MAP[labels[cell_indx]].get('formatter')
            value = formatter(cell) if formatter is not None else cell
            if type(value) == datetime.datetime:
                # worksheet.write(row_indx+1, cell_indx, value, date_format)
                worksheet.write(row_indx+1, cell_indx, (value-datetime.datetime.fromtimestamp(0.0)).total_seconds())
            else:
                worksheet.write(row_indx+1, cell_indx, value)

    object_1_sum = convert_time(data[f1][13])
    # object_2_sum = convert_time(data[f2][13])
    last_event_end = convert_time(data[last_event][11])
    worksheet.write_string(0 ,16 , "object 1 sum", header_format)
    worksheet.write_datetime(0, 17, object_1_sum, date_format)
    # worksheet.write_string(1 ,16 , "object 2 sum", header_format)
    # worksheet.write_datetime(1, 17, object_2_sum, date_format)
    # worksheet.write_string(2 ,  16, "time to reach 20s", header_format)
    worksheet.write_datetime(2 ,  17, last_event_end, date_format)

    # assert data[f1][13] + data[f2][13] == TIME_LIMIT * 1000000.0
    summary_worksheet.write_string(1+file_indx, 0, os.path.basename(input_file.name))
    # summary_worksheet.write_datetime(1+file_indx, 1, object_1_sum, date_format)
    summary_worksheet.write(1+file_indx, 1, (object_1_sum-datetime.datetime.fromtimestamp(0.0)).total_seconds())
    # summary_worksheet.write_datetime(1+file_indx, 2, object_2_sum, date_format)
    # summary_worksheet.write_datetime(1+file_indx, 2, last_event_end, date_format)
    summary_worksheet.write(1+file_indx, 2, (last_event_end-datetime.datetime.fromtimestamp(0.0)).total_seconds())



# Commands

@click.group()
def process():
    pass

def _convert_dataset_to_xls(input_folder, output_file):
    files_to_process = [f for f in os.listdir(input_folder) if not f.startswith('.')]

    # prepare the excel workbook
    workbook = xlsxwriter.Workbook(output_file)
    header = workbook.add_format({'bold': True, 'border': True})
    summary_worksheet = workbook.add_worksheet("summary")
    summary_worksheet.set_column('A:A', 30.0)
    summary_worksheet.set_column('B:D', 22.0)

    # for indx, label in enumerate(['filename', 'object 1 exploration time', 'object 2 exploration time', 'time to reach 20s']):
    for indx, label in enumerate(['filename', 'object 1 exploration time', 'time to reach 5 mins']):
        summary_worksheet.write_string(0, indx, label, header)

    with click.progressbar(files_to_process, label="processing csv files") as bar:
        for indx, input_filename in enumerate(bar):
            with open(os.path.join(input_folder, input_filename), newline='') as csvfile:
                process_data_file(csvfile, workbook, summary_worksheet, file_indx=indx, time_limit=20, header_format=header)

    workbook.close()

@process.command()
@click.argument('input_folder')
@click.argument('output_file')
def convert_dataset_to_xls(input_folder, output_file):
    _convert_dataset_to_xls(input_folder, output_file)


if __name__ == "__main__":
    process()

    # print(files_to_process)
    # issue_counter = 0
    # def dump_date(d):
    #     if isinstance(d, int):
    #         return d
    #     return int((datetime.datetime.fromtimestamp(0) + d).timestamp()*1000000)

    # for file_indx, input_filename in enumerate(files_to_process[0:]):
    #     # print(input_filename)
    #     # for input_file
    #     CSV_INPUT_FILE = input_filename
    #     labels = []
    #     TIME_LIMIT = 20


    #     with open(SOURCE_FILES_FOLDER + CSV_INPUT_FILE, newline='') as csvfile:
    #         data = load_data(csvfile)
    #         try:
    #             # print(data)
    #             data = fix_data(data, input_filename=input_filename)
    #             verify_data(data)
    #             # print(csvfile)
    #         except Exception as e:
    #             issue_counter += 1
    #             print("{}:  experiment start at: {} , last_event_ends: {}, reached duration of: {}".format(input_filename, data.at[0, 'start_time'], data['end_time'].max(), data['duration_sum'].max()))
    #             # verify_data(data)
    #
    #             # print("{} failed !".format(csvfile))
    #             # print(data)
    #             traceback.print_exc()
    #             break

    #
    #         data = data.applymap(dump_date)
    #         # print(data)
    #         data.to_csv(OUTPUT_DIRECTORY + input_filename, index=False)

    #            # print(e.traceback)
    # print("encountered {} issues".format(issue_counter))
