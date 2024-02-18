import json
import numpy as np
import os
from datetime import date, timedelta
from extract_prices import get_previous_data, extract_dates_from_date_range, extract_price_data, save_json
from extract_prices import save_unresponsive, save_wrong_dates


def get_final_date(data_dict):
    final_date = '2015-03-19'
    for key in data_dict.keys():
        final_date_for_fund = list(data_dict[key].keys())[-1]
        if(final_date_for_fund > final_date):
            final_date = final_date_for_fund
    return final_date


def get_price_data_from_json():
    filepath = 'historical_prices.json'
    if not os.path.exists(filepath):
        print('Historical prices json file is not available')
        return None
    else:
        with open(filepath, 'r') as fid:
            data_dict = json.load(fid)
    return data_dict


def extract_fund_prices(data_dict, fund_name):
    fund_dict = data_dict[fund_name]
    dates = list(fund_dict.keys())
    price_array = np.zeros((len(dates), 3), dtype=object)
    for i in range(len(dates)):
        price_array[i, 0] = dates[i]
        price_array[i, 1] = fund_dict[dates[i]][0]
        price_array[i, 2] = fund_dict[dates[i]][1]
    return price_array


def get_fund_names(data_dict):
    fund_names = list(data_dict.keys())
    fund_names.sort()
    return fund_names


def update_price_json(self):
    start_date = '2015-03-16'
    end_date = str(date.today())
    previous_data, start_date = get_previous_data(start_date)
    date_list = extract_dates_from_date_range(start_date, end_date)
    appended_data = extract_price_data(date_list, previous_data, self)
    save_json(appended_data)
    save_unresponsive()
    save_wrong_dates()


def check_sync_requirement(curr_date_str):
    today_date = date.today()
    # today_date = date(2016, 3, 31)
    yesterday_date = today_date - timedelta(days=1)
    if(curr_date_str < str(yesterday_date)):
        sync_required = True
    else:
        sync_required = False
    return sync_required


if __name__ == '__main__':
    data_dict = get_price_data_from_json()
    price_array = extract_fund_prices(data_dict, 'Ceybank Century Growth')
    b = 9