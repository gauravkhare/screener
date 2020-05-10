# from nsetools import Nse
from pprint import pprint
from collections import OrderedDict
from nsepy.derivatives import  get_expiry_date
import os
import numpy as np
import schedule as schedule
from nsepy import get_history, get_quote
from datetime import date, timedelta, datetime
# import schedule, time
import sched, time
# import matplotlib.pyplot as plt
import pandas as pd
import telegram_send
# import datetime


# telegram_send.configure('Analysis_Script')
# telegram_send.send(conf='telegram.conf',messages=['livedata7.py script started'])

pd.set_option('display.max_columns', 50)

# Code to fetch all the Nifty50 codes
niftyCodesPath = r'../data/Nifty50.csv'

startDate = date.today() - timedelta(5)  # last 5th day
endDate = date.today()

dyn_file_name = 'intraday7_' + str(endDate) + '.txt'

if os.path.exists(dyn_file_name):
    append_write = 'a' # append if already exists
else:
    append_write = 'w' # make a new file if not


sourceFile = open(dyn_file_name, append_write)
if append_write == 'w':
    print('{: <10},{: <21},{: <7},{: <8},{: <8},{: <8},{: <8},{: <8},{: <7},{: <8},{: <8},{: <8},{: <8},{: <12}'
      .format('UNDERLYING',
            'TIMESTAMP',
            'OPEN',
            'HIGH',
            'LOW',
            'LAST',
            'VOL',
            'AVGVOL',
            'VOLSGNL',
            'CHOI',
            '%PR',
            '%OI',
            '%VOL',
            'MON_INV_MLL'), file=sourceFile)

sourceFile.flush()
stk_ts_dict = {}
factor = 2  # times vol should be higher than avg, in order to be statictically significant
mkt_hrs = [9, 10, 11, 12, 13, 14, 15]

def calc_avg_vol_wrt_time(avg_vol):
    """
    :param avg_vol: int
    :return: the effective avg volume number which can be considered for comparison and infer that increase in vol is
    not by chance but due to some forced buying/selling
    """
    mkt_hr = int(datetime.fromtimestamp(time.time()).strftime('%H'))
    unit = avg_vol / 7
    if mkt_hr in mkt_hrs:
        eff_avg_vol = unit * (mkt_hrs.index(mkt_hr)+1) * factor
    else:
        eff_avg_vol = avg_vol * factor
    return eff_avg_vol

def get_nifty_scrips(niftyCodesPath):
    # niftyCodes = pd.DataFrame.from_csv(niftyCodesPath)
    niftyCodes = pd.read_csv(niftyCodesPath)
    niftyCodes = niftyCodes[niftyCodes.CompanyName.str.contains('^(?!#).*')]
    niftyCodes['index'] = np.arange(len(niftyCodes))  # adding a column to assign row number
    # print(niftyCodes)
    niftyCodes = niftyCodes.reset_index().set_index('index')
    # print(niftyCodes)
    niftyCodes = niftyCodes.iloc[:, [0, 3, 4]]  # Choosing 0th, 3rd, 4th column of df
    # print(niftyCodes)
    return niftyCodes


nifty_codes = get_nifty_scrips(niftyCodesPath)
print(nifty_codes[2:])

today =  date.today()
currentExpiryDateSet = get_expiry_date(today.year, today.month)
currentExpiryDate = sorted(currentExpiryDateSet, reverse=True)[0]

def fetch_periodic_data(nifty_codes):
    sourceFile = open(dyn_file_name, 'a+')
    source_file_consolidate = open('LiveDataConsolidated.txt', 'w')
    print('{: <10},{: <21},{: <7},{: <8},{: <8},{: <8},{: <8},{: <8},{: <7},{: <8},{: <8},{: <8},{: <8},{: <12}'
          .format('UNDERLYING',
            'TIMESTAMP',
            'OPEN',
            'HIGH',
            'LOW',
            'LAST',
            'VOL',
            'AVGVOL',
            'VOLSGNL',
            'CHOI',
            '%PR',
            '%OI',
            '%VOL',
            'MON_INV_MLL'), file=source_file_consolidate)
    sourceFile.flush()
    ts = time.time()
    st = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
    print("fetchPeriodicData started @ ", st)

    for index, row in nifty_codes.iterrows():
        # Historical data to get average volume of last 3 days
        historicalData = get_history(symbol=row['Symbol'], start=startDate, end=endDate, futures=True,
                                     expiry_date=currentExpiryDate)
                                     # expiry_date=datetime(2020, 5, 28))
        avgVolume = pd.DataFrame.mean(historicalData['Number of Contracts'])

        liveData = get_quote(symbol=row['Symbol'], instrument='FUTSTK', expiry=currentExpiryDate, option_type='-',
                             strike=100)
        # print("keys :: ", liveData)
        volume = 0 if liveData.get('numberOfContractsTraded') is None else liveData.get('numberOfContractsTraded')

        if volume > calc_avg_vol_wrt_time(avgVolume) and liveData.get('underlying') not in stk_ts_dict.keys():
            stk_ts_dict[liveData.get('underlying')] = liveData.get('lastPrice')
            msg = liveData.get('underlying') + ' crossed volume at '+ \
                  datetime.fromtimestamp(ts).strftime('%H:%M ') \
                  + str(liveData.get('lastPrice'))
            # telegram_send.send(conf='telegram.conf', messages=[msg])


        try:
            print('{: <10},{: <21},{: <7},{: <8},{: <8},{: <8},{: <8},{: <8},{: <7},{: <8},{: <8},{: <8},{: <8},{: <12}'
                  .format(liveData.get('underlying'),
                          datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), #liveData.get('lastUpdateTime')
                          liveData.get('openPrice'),
                          liveData.get('highPrice'),
                          liveData.get('lowPrice'),
                          liveData.get('lastPrice'),
                          liveData.get('numberOfContractsTraded'),
                          int(avgVolume),
                          stk_ts_dict[liveData.get('underlying')] if calc_avg_vol_wrt_time(avgVolume) < volume else '',
                          liveData.get('changeinOpenInterest'),
                          liveData.get('pChange'),
                          liveData.get('pchangeinOpenInterest'),
                          int(liveData.get('numberOfContractsTraded')*100/int(avgVolume)),
                          abs(int((liveData.get('changeinOpenInterest')*liveData.get('lastPrice'))/1000000))), file=sourceFile)
            print('{: <10},{: <21},{: <7},{: <8},{: <8},{: <8},{: <8},{: <8},{: <7},{: <8},{: <8},{: <8},{: <8},{: <12}'
                  .format(liveData.get('underlying'),
                          datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),
                          liveData.get('openPrice'),
                          liveData.get('highPrice'),
                          liveData.get('lowPrice'),
                          liveData.get('lastPrice'),
                          liveData.get('numberOfContractsTraded'),
                          int(avgVolume),
                          stk_ts_dict[liveData.get('underlying')] if calc_avg_vol_wrt_time(avgVolume) < volume else '',
                          liveData.get('changeinOpenInterest'),
                          liveData.get('pChange'),
                          liveData.get('pchangeinOpenInterest'),
                          int(liveData.get('numberOfContractsTraded') * 100 / int(avgVolume)),
                          abs(int((liveData.get('changeinOpenInterest') * liveData.get('lastPrice')) / 1000000))), file=source_file_consolidate)

        except:
            print('{: <10},{: <21},{: <7},{: <8},{: <8},{: <8},{: <8},{: <8},{: <7},{: <8},{: <8},{: <8},{: <8},{: <12}'
                  .format(row['Symbol'],
                          datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S'),
                          "" if liveData.get('openPrice') is None else liveData.get('openPrice'),
                          "" if liveData.get('highPrice') is None else liveData.get('highPrice'),
                          "" if liveData.get('lowPrice') is None else liveData.get('lowPrice'),
                          "" if liveData.get('lastPrice') is None else liveData.get('lastPrice'),
                          "" if liveData.get('numberOfContractsTraded') is None else liveData.get(
                              'numberOfContractsTraded'),
                          "" if avgVolume is None else int(avgVolume),
                          '',
                          "" if liveData.get('changeinOpenInterest') is None else liveData.get('changeinOpenInterest'),
                          "" if liveData.get('pChange') is None else liveData.get('pChange'),
                          "" if liveData.get('pchangeinOpenInterest') is None else liveData.get(
                              'pchangeinOpenInterest'),
                          '',
                          ''), file=sourceFile)
            print('{: <10},{: <21},{: <7},{: <8},{: <8},{: <8},{: <8},{: <8},{: <7},{: <8},{: <8},{: <8},{: <8},{: <12}'
                  .format(row['Symbol'],
                          datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S'),
                          "" if liveData.get('openPrice') is None else liveData.get('openPrice'),
                          "" if liveData.get('highPrice') is None else liveData.get('highPrice'),
                          "" if liveData.get('lowPrice') is None else liveData.get('lowPrice'),
                          "" if liveData.get('lastPrice') is None else liveData.get('lastPrice'),
                          "" if liveData.get('pChange') is None else liveData.get('pChange'),
                          "" if liveData.get('pchangeinOpenInterest') is None else liveData.get(
                              'pchangeinOpenInterest'),
                          "" if liveData.get('numberOfContractsTraded') is None else liveData.get(
                              'numberOfContractsTraded'),
                          "" if avgVolume is None else int(avgVolume),
                          '',
                          "" if liveData.get('changeinOpenInterest') is None else liveData.get('changeinOpenInterest'),
                          "" if liveData.get('pChange') is None else liveData.get('pChange'),
                          "" if liveData.get('pchangeinOpenInterest') is None else liveData.get(
                              'pchangeinOpenInterest'),
                          '',
                          ''), file=source_file_consolidate)

        sourceFile.flush()
        source_file_consolidate.flush()
    sourceFile.close()
    source_file_consolidate.close()

fetch_periodic_data(nifty_codes)


schedule.every(100).seconds.do(fetch_periodic_data,nifty_codes)
while True:
    schedule.run_pending()
    time.sleep(1)
#
#
# while 1:
#     fetch_periodic_data(nifty_codes)
#     time.sleep(100)
