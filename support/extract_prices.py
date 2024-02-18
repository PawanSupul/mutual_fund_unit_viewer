from datetime import date, timedelta
import requests
from bs4 import BeautifulSoup
import numpy as np
import json
import os

retry_count = 0
retry_limit = 3
unresponsive_dates = []
errorneous_dates = []
dynamic_file_directory_path = 'dynamic/'


def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)


def extract_dates_from_date_range(start_date, end_date):
    date_list = []
    start = date(int(start_date.split('-')[0]), int(start_date.split('-')[1]), int(start_date.split('-')[2]))
    finish = date(int(end_date.split('-')[0]), int(end_date.split('-')[1]), int(end_date.split('-')[2]))
    for single_date in daterange(start, finish):
        date_string = single_date.strftime("%Y-%m-%d")
        date_list.append(date_string)
    return date_list


def scrape_date_url(url):
    global retry_count, unresponsive_dates
    response = requests.get(url)
    if (response.status_code != 200):
        if(retry_count < retry_limit):
            retry_count += 1
            scrape_date_url(url)
        else:
            print(f'Warning! Response : {response.status_code} for url : {url}')
            unresponsive_dates.append(url)
        table_data = []
        web_date = '1970-01-01'
    else:
        retry_count = 0
        soup = BeautifulSoup(response.content, 'html.parser')
        table = soup.find("table")
        table_data = []
        for row in table.find_all('tr', class_=lambda x: x not in ['title-main', 'hdr-bg-b']):
            row_data = []
            for cell in row.find_all(['td', 'th']):
                row_data.append(cell.get_text(strip=True))
            if(row_data):
                if(len(row_data) == 1):
                    split_list = row_data[0].split('Prices as on')
                    if(len(split_list) == 2):
                        web_date_string =  split_list[-1]
                        web_date_list = web_date_string.split('/')
                        web_date = f'{web_date_list[2].strip()}-{web_date_list[0].strip()}-{web_date_list[1].strip()}'
                elif(len(row_data) != 3):
                    print(f'Error! Unpredicted data format encountered: {row_data}')
                else:
                    table_data.append(row_data)
    return table_data, web_date


def clean_and_prepare_data(data_list):
    data_array = np.asarray(data_list)
    for i in range(data_array.shape[0]):
        selling = data_array[i, 1].split(' ')[0].replace(',', '')
        buying = data_array[i, 2].split(' ')[0].replace(',', '')
        data_array[i, 1] = selling
        data_array[i, 2] = buying
    return data_array


def concat_dict_data(previous_data, data_array, webdate):
    global errorneous_dates
    date_dict = {}
    for i in range(data_array.shape[0]):
        if(data_array[i, 1].lower() == 'ex.div' or data_array[i, 2].lower() == 'ex.div'):
            continue
        elif('..' in data_array[i, 1] or '..' in data_array[i, 2]):
            data_array[i, 1] = data_array[i, 1].replace('..', '.')
            data_array[i, 2] = data_array[i, 2].replace('..', '.')
        try:                                                                              ## uncomment this in production
            fund_dict = {webdate: [float(data_array[i, 1]), float(data_array[i, 2])]}
            date_dict[data_array[i, 0]] = fund_dict
        except:
            errorneous_dates.append(webdate)
            print(f'Warning! Conversion error on date: {webdate} - Ex: {data_array[i, 1]} | Added to the Erroneous dates file and excluded from database.')
            continue

    for key in date_dict:
        if(key in previous_data.keys()):
            curr_date = list(date_dict[key].keys())[0]
            existing_dict = previous_data[key]
            existing_dict[curr_date] = date_dict[key][curr_date]
            previous_data[key] = existing_dict
        else:
            previous_data[key] = date_dict[key]
    return previous_data


def extract_price_data(date_list, previous_data, self=None, gui=False):
    for c, date_string in enumerate(date_list):
        if(gui):
            self.lbl_status['text'] = f'Now syncing date = {date_string} : {c + 1}/{len(date_list)}'
            self.lbl_date['text'] = date_string
            self.master.update()
        else:
            print(f'Now processing date = {date_string} : {c + 1}/{len(date_list)}')
        [year, month, day] = date_string.split('-')
        url = f'http://utasl.lk/reports/index3.php?date={month}%2F{day}%2F{year}'
        data_list, web_date = scrape_date_url(url)
        if(web_date == '1970-01-01'):
            continue
        assert date_string == web_date
        data_array = clean_and_prepare_data(data_list)
        previous_data = concat_dict_data(previous_data, data_array, date_string)
    return previous_data

def save_json(data_dict):
    with open(dynamic_file_directory_path + 'historical_prices.json', 'w') as fid:
        json.dump(data_dict, fid)
    # print(f'>>> Data json saved')

def save_unresponsive(overwrite = False):
    global unresponsive_dates
    filepath = dynamic_file_directory_path + 'unresponsive.txt'
    if os.path.exists(filepath):
        if(overwrite):
            with open(filepath, 'w') as fid:
                fid.writelines(s + '\n' for s in unresponsive_dates)
        else:
            with open(filepath, 'a') as fid:
                fid.writelines(s + '\n' for s in unresponsive_dates)
    else:
        with open(filepath, 'w') as fid:
            fid.writelines(s + '\n' for s in unresponsive_dates)
    # print(f'>>> Unresponsive files saved')

def save_wrong_dates(overwrite = False):
    global errorneous_dates
    filepath = dynamic_file_directory_path + 'wrong_dates.txt'
    if os.path.exists(filepath):
        if(overwrite):
            with open(filepath, 'w') as fid:
                fid.writelines(s + '\n' for s in errorneous_dates)
        else:
            with open(filepath, 'a') as fid:
                fid.writelines(s + '\n' for s in errorneous_dates)
    else:
        with open(filepath, 'w') as fid:
            fid.writelines(s + '\n' for s in errorneous_dates)
    # print(f'>>> Erroneous dates files saved')


def read_json():
    filepath = dynamic_file_directory_path + 'historical_prices.json'
    if not os.path.exists(filepath):
        data_dict = {}
    else:
        with open(filepath, 'r') as fid:
            data_dict = json.load(fid)
    return data_dict

def get_previous_data(start_date):
    data_dict = read_json()
    most_recent = '2015-01-01'
    for key in data_dict.keys():
        for individual_date in list(data_dict[key].keys()):
            dates = [most_recent]
            dates.append(individual_date)
            sorteddates = np.sort(dates)
            most_recent = sorteddates[-1]
    if(most_recent > start_date):
        start_date = most_recent
    return data_dict, start_date

def main():
    start_date = '2015-03-16'
    end_date = '2021-12-30'
    previous_data, start_date = get_previous_data(start_date)
    date_list = extract_dates_from_date_range(start_date, end_date)
    appended_data = extract_price_data(date_list, previous_data)
    save_json(appended_data)
    save_unresponsive()
    save_wrong_dates()

def test():
    jsondata = read_json()
    b = 9

if __name__ == '__main__':
    main()
