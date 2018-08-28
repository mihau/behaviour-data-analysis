#!/usr/bin/env python
import csv
import xlwt
import time
import datetime
from dateutil import parser
import xlsxwriter
import os
from pprint import pprint

import pandas as pd

SOURCE_FILES_FOLDER = '/Users/mszymans/csvs/'
OUTPUT_FILE = '/Users/mszymans/processed.xlsx'

def convert_time(t):
    return datetime.datetime.fromtimestamp(float(t)/1000000.0)

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

files_to_process = os.listdir(SOURCE_FILES_FOLDER)[1:]
workbook = xlsxwriter.Workbook(OUTPUT_FILE)
header = workbook.add_format({'bold': True, 'border': True})

# class ExplorationEvent(object):
#     def __init__(self):


summary_worksheet = workbook.add_worksheet("summary")
summary_worksheet.set_column('A:A', 30.0)
summary_worksheet.set_column('B:D', 22.0)

for indx, label in enumerate(['filename', 'object 1 exploration time', 'object 2 exploration time', 'time to reach 20s']):
    summary_worksheet.write_string(0, indx, label, header)

def process_data(input_file):
    data = pd.read_csv(
        input_file,
        sep=',',
        parse_dates=[1, 2, 3, 4, 5, 6, 7, 9, 10, 11, 12, 13],
    )
    print(data.start_time)


def process_data_file(input_file):
    reader = csv.reader(csvfile, delimiter=',')
    data = []
    for idx, row in enumerate(reader):
        if idx == 0:
            labels = row
        else:
            data.append(row)
    # workbook = xlwt.Workbook()
    worksheet_name = ''.join(CSV_INPUT_FILE.split('.')[0:2])
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
    f2, o2 = mark_last_event(data, 2)
    # print(f1, f2)
    last_event = None
    if int(data[f1][2]) > int(data[f2][2]):
        if o1 and o2:
            data[f1-1][14] = 1
            data[f1][14] = 0
            f1 = f1 - 1
        last_event = f1
    else:
        if o1 and o2:
            data[f2-1][14] = 2
            data[f2][14] = 0
            f2 = f2 - 1
        last_event = f2
        
    if int(data[f1][2]) > int(data[f2][2]):
        last_event = f1
    else:
        last_event = f2


    # pprint(data)



    # set labels on top of the files   
    for indx, label in enumerate(labels):
        worksheet.write_string(0, indx, LABEL_MAP.get(label).get('label'), header)

    for row_indx, row in enumerate(data):
        assert int(row[1]) - int(row[0]) == int(row[4])  # check if duration is ok
        # assert int(row[4]) - int(row[])
        for cell_indx, cell in enumerate(row):
            #print(labels[cell_indx])
            formatter = LABEL_MAP[labels[cell_indx]].get('formatter')
            #print(cell)
            value = formatter(cell) if formatter is not None else cell
            #print(type(value))
            #print(value)
            #print(row_indx+1, cell_indx)
            if type(value) == datetime.datetime:
                worksheet.write_datetime(row_indx+1, cell_indx, value, date_format)
            else:
                worksheet.write(row_indx+1, cell_indx, value)

    object_1_sum = convert_time(data[f1][13])
    object_2_sum = convert_time(data[f2][13])
    last_event_end = convert_time(data[last_event][11])
    worksheet.write_string(0 ,16 , "object 1 sum", header)
    worksheet.write_datetime(0, 17, object_1_sum, date_format)
    worksheet.write_string(1 ,16 , "object 2 sum", header)
    worksheet.write_datetime(1, 17, object_2_sum, date_format)
    worksheet.write_string(2 ,  16, "time to reach 20s", header)
    worksheet.write_datetime(2 ,  17, last_event_end, date_format)

    # assert data[f1][13] + data[f2][13] == TIME_LIMIT * 1000000.0
    print(data[f1][13] + data[f2][13])
    summary_worksheet.write_string(1+file_indx, 0, input_filename)
    summary_worksheet.write_datetime(1+file_indx, 1, object_1_sum, date_format)
    summary_worksheet.write_datetime(1+file_indx, 2, object_2_sum, date_format)
    summary_worksheet.write_datetime(1+file_indx, 3, last_event_end, date_format)


if __name__ == "__main__":
    # print(files_to_process)
    for file_indx, input_filename in enumerate(files_to_process[0:1]):
        print(input_filename)
        # for input_file
        CSV_INPUT_FILE = input_filename
        labels = []
        TIME_LIMIT = 20

        with open('/Users/mszymans/csvs/' + CSV_INPUT_FILE, newline='') as csvfile:
            process_data(csvfile)

        # f1_format = workbook.add_format({'bg_color': 'green'})
        # worksheet.set_row(f1_1, None, f1_format)

        
    workbook.close()