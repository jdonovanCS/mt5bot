import yfinance as yf
import os
import json
import time
import pandas_datareader.data as web
import pandas as pd
import math

import datetime
import numpy as np
from scipy.stats import norm


# Location of settings.json
settings_filepath = "settings.json" # <- This can be modified to be your own settings filepath


# Function to import settings from settings.json
def get_project_settings(import_filepath):
    """
    Function to import settings from settings.json
    :param import_filepath: path to settings.json
    :return: settings as a dictionary object
    """
    # Test the filepath to make sure it exists
    if os.path.exists(import_filepath):
        # If yes, import the file
        f = open(import_filepath, "r")
        # Read the information
        project_settings = json.load(f)
        # Close the file
        f.close()
        # Return the project settings
        return project_settings
    # Notify user if settings.json doesn't exist
    else:
        raise ImportError("settings.json does not exist at provided location")



def calculate_delta(option_type, S, K, T, r, sigma):
    d1 = (np.log(S/K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    if option_type == 'call':
        return norm.cdf(d1)
    elif option_type == 'put':
        return norm.cdf(d1) - 1


project_settings = get_project_settings(import_filepath=settings_filepath)

# # Initialize the polygon.io client
# client = polygon.RESTClient(api_key="AkeRGpCLIo4L7TEAyd6nzpBctsnMJtO_")

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

yf_ticker = yf.Ticker('cost')

print(yf_ticker.options)

count = 0
# while datetime.datetime.strptime(yf_ticker.options[count], "%Y-%m-%d").date() - datetime.date.today() < datetime.timedelta(190):
#     if calls is None:
#         calls = pd.DataFrame(yf_ticker.option_chain(date=yf_ticker.options[count]))
#     else:
#         calls = calls + yf_ticker.option_chain(date=yf_ticker.options[count])


# only gets calls expiring this day.
options_chain = yf_ticker.option_chain(date='2024-12-27')

# print(pd.DataFrame(options_chain.calls)[['volume', 'strike']])

# options_chain = yf_ticker.option_chain(date=dte_50)

# print(pd.DataFrame(options_chain.calls)[['volume', 'strike']])


sofr_data = web.DataReader('SOFR', 'fred', datetime.datetime.today()-datetime.timedelta(days=2), datetime.datetime.today())
print(sofr_data.tail())
risk_free_rate = sofr_data['SOFR'][-1]
print(risk_free_rate)


calls = pd.DataFrame(options_chain.calls).sort_values(by=['strike'])



puts  = pd.DataFrame(options_chain.puts).sort_values(by=['strike'])


current_price = yf_ticker.info['currentPrice']
print(f"Current price: {current_price}")

print(calls.columns)

calls = calls[(calls['strike'] > current_price - current_price*.15) & (calls['strike'] < current_price + current_price*.15)]
puts = puts[(puts['strike'] > current_price - current_price*.15) & (puts['strike'] < current_price + current_price*.15)]


# I think I'm doing time to expiry correctly now.. see keep for original ai-generated code.
calls['delta'] = calls.apply(lambda row: calculate_delta('call', current_price, row['strike'], 
                                                        ((datetime.datetime.strptime('2024-12-27', "%Y-%m-%d") - pd.Timestamp.today()).days / 365), 
                                                        risk_free_rate, row['impliedVolatility']), axis=1)


puts['delta'] = puts.apply(lambda row: calculate_delta('put', current_price, row['strike'], 
                                                        ((datetime.datetime.strptime('2024-12-27', "%Y-%m-%d") - pd.Timestamp.today()).days / 365), 
                                                        risk_free_rate, row['impliedVolatility']), axis=1)



calls['volume'] = calls['volume'].fillna(0)
puts['volume'] = puts['volume'].fillna(0)

calls['delta_dollars'] = (calls['delta']+calls['lastPrice'])*calls['volume']*100
puts['delta_dollars'] = (puts['delta']-puts['lastPrice'])*puts['volume']*100*-1

print(calls[['strike', 'lastPrice', 'volume', 'openInterest', 'delta', 'delta_dollars', 'lastTradeDate']])
print(puts[['strike', 'lastPrice', 'volume', 'openInterest', 'delta', 'delta_dollars']])

# combined = pd.DataFrame(columns=['volume_put', 'volume_call', 'delta_put', 'delta_call', 'strike', 'last_price_put', 'last_price_call'])
# for i, row in calls.iterrows():

#     if not math.isnan(row['strike']) and round(row['strike'], 1) in round(puts['strike'],1):
        
#         strike = row['strike']
#         volume_put = puts[puts['strike'] == row['strike']]['volume'].values
#         volume_call = calls[calls['strike'] == row['strike']]['volume'].values
#         delta_put = puts[puts['strike'] == row['strike']]['delta'].values
#         delta_call = calls[calls['strike'] == row['strike']]['delta'].values
#         last_price_put = puts[puts['strike'] == row['strike']]['lastPrice'].values
#         last_price_call = calls[calls['strike'] == row['strike']]['lastPrice'].values
#         if volume_put.size > 0 and volume_call.size > 0 and not math.isnan(volume_put[0]) and not math.isnan(volume_call[0]):
#             combined = pd.concat([combined, pd.DataFrame([{'strike': strike, 'volume_put': volume_put[0], 'volume_call': volume_call[0], 'delta_put': delta_put[0], 'delta_call': delta_call[0], 'last_price_put': last_price_put[0], 'last_price_call': last_price_call[0]}])])
        
# combined['delta_dollars_put'] = (combined['delta_put']+current_price+combined['last_price_put']) * combined['volume_put']
# combined['delta_dollars_call'] = (combined['delta_call']+current_price+combined['last_price_call']) * combined['volume_call']
# combined['delta_dollars_diff'] = combined['delta_dollars_call'] - combined['delta_dollars_put']

# combined['difference_in_volume'] = combined['volume_call'] - combined['volume_put']
# print('positive value in difference means higher call, negative means higher put')
# print(combined)




# # Get options data for a symbol
# options_data = client.list_options_contracts(underlying_ticker="AAPL")

# for contract in options_data:
#     print(contract)