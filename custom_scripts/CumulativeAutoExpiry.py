
from nsepy import get_history,get_quote
from nsepy.derivatives import  get_expiry_date
from datetime import date,timedelta,datetime
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pylab
import numpy as np

def plotTheGraph(stock):
        today =  date.today()
        currentExpiryDate = get_expiry_date(today.year, today.month)
        # if(today>currentExpiryDate):
        #     currentExpiryDate = get_expiry_date(today.year,today.month+1)
        #     prevExpiryDate = get_expiry_date(today.year,today.month)
        #     futureExpiryDate = get_expiry_date(today.year, today.month + 2)
        # else :
        #     currentExpiryDate = get_expiry_date(today.year, today.month)
        #     prevExpiryDate = get_expiry_date(today.year, today.month-1)
        #     if(today.month != 12):
        #         futureExpiryDate = get_expiry_date(today.year, today.month + 1)
        #     else:
        #         futureExpiryDate = get_expiry_date(today.year+1, 1)

        currentExpiryDateSet = get_expiry_date(today.year, today.month)
        prevExpiryDateSet = get_expiry_date(today.year, today.month - 1)
        if (today.month != 12):
            futureExpiryDateSet = get_expiry_date(today.year, today.month + 1)
        else:
            futureExpiryDateSet = get_expiry_date(today.year+1, 1)

        currentExpiryDate = sorted(currentExpiryDateSet, reverse=True)[0]
        prevExpiryDate = sorted(prevExpiryDateSet, reverse=True)[0]
        futureExpiryDate = sorted(futureExpiryDateSet, reverse=True)[0]


        start = prevExpiryDate-timedelta(15)
        end = today #date(2018,12,27)
        print('start',start)
        print('end',end)
        end2=today

        index =False
        future = True

        instrument = 'FUTSTK'
        instrumentArray = ['NIFTY','BANKNIFTY']
        if stock in instrumentArray:
            instrument = 'FUTIDX'
            index = True
            future = False


        # Live Data
        liveData = get_quote(symbol=stock, instrument=instrument, expiry=currentExpiryDate, option_type='-',
                             strike=700)

        #Pivot table code
        liveData = pd.DataFrame.from_dict(liveData,orient='index')
        # liveData = pd.DataFrame(liveData,columns=['column','values'])
        # liveData['index'] = np.arange(len(liveData))
        # liveData = liveData.reset_index().set_index('index')

        # liveData.pivot(columns='level_0',values='0')
        # print(liveData)

        ltp = liveData.get('ltp',0)
        volume = liveData.get('numberOfContractsTraded',0)
        # print("Today's volume: ",volume)
        chngOI = liveData.get('changeinOpenInterest',0)
        # print("Today's OI: ",chngOI)

        # print("live: ",liveData)
        # print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")

        data_fut = get_history(symbol=stock,index= index ,futures=future,start=start, end=end,
        expiry_date=currentExpiryDate)
        data_fut2 = get_history(symbol=stock,index= index,futures=future,start=start, end=end2,
        expiry_date=futureExpiryDate)

        # pd.DataFrame(data_fut, index=data_fut['Date'].strftime("%b %d")).style.format("{:.2}")
        # pd.DataFrame(data_fut2, index=data_fut..strftime("%b %d")).style.format("{:.2}")

        if instrument == 'FUTSTK':
            OI_combined = pd.concat([data_fut2['Open Interest'], data_fut['Open Interest']], axis=1, sort=False)
            OI_combined['OI_Combined'] = OI_combined.sum(axis=1) + int(chngOI)
            # print("Open Interest: ",OI_combined['OI_Combined'])
            # OI_combined['OI_Combined'] = OI_combined['OI_Combined'] + chngOI

            # No. of contracts
            volume_combined= pd.concat([data_fut2['Number of Contracts'],data_fut['Number of Contracts']],axis=1,sort=False)
            volume_combined['volume_combined']=volume_combined.sum(axis=1) + int(volume)
            # print("Volume : ",volume_combined['volume_combined'])
            # print("volume_combined['volume_combined'] = ",volume_combined['volume_combined'])
            # volume_combined['volume_combined'] = volume_combined['volume_combined'] + volume
        else:
            # No. of contracts
            volume_combined = pd.concat([data_fut2['Volume'], data_fut['Volume']], axis=1,
                                        sort=False)
            volume_combined['volume_combined'] = volume_combined.sum(axis=1)
            # print("volume_combined['volume_combined'] = ",volume_combined['volume_combined'])
            # volume_combined['volume_combined'] = volume_combined['volume_combined'] + volume

        # Rule to throw an alert
        # Display Underlying
        plt.subplot(222)
        plt.title('Underlying')
        # priceCombined= pd.concat([data_fut['Underlying'],data_fut2['Underlying']],axis=1,sort=False)
        # plt.plot(priceCombined,color='green')
        plt.plot(data_fut['Last'], color='green')
        # plt.plot(pd.concat(data_fut['Last'],liveData.get('ltp',0)), color='green')
        plt.legend(['Last'])
        plt.xlabel('Date')
        plt.ylabel('Price')
        # plt.xlabel.set_major_formatter(mdates.DateFormatter('%b %d'))

        # Display Volumes
        plt.subplot(224)
        plt.title('Volume')
        plt.plot(volume_combined.volume_combined,label='Volume',color='blue')
        plt.plot(volume_combined.volume_combined.rolling(5).mean(),label='Volume',color='orange')
        plt.legend(['Volume','Volume_mean'])
        plt.xlabel('Date')
        plt.ylabel('Volume')
        # plt.xlabel.set_major_formatter(mdates.DateFormatter('%b %d'))

        # Display Cumulative Open Interest
        plt.figure(1,figsize=(10,9))
        plt.subplot(221)
        plt.title('Open Interest')
        plt.plot(OI_combined.OI_Combined,label='OI')
        plt.plot(OI_combined.OI_Combined.rolling(5).mean(),label='OI')

        plt.xlabel('Date')
        plt.ylabel('Open Interest')
        # plt.xlabel.set_major_formatter(mdates.DateFormatter('%b %d'))

        fig = pylab.gcf()
        fig.canvas.set_window_title(stock)
        plt.legend(['OI','OI_mean'])

        plt.show()
        stock = input("Enter the Future Symbol here: ")
        if stock == "":
            plt.close(fig)
            return
        else:
            plt.close(fig)
            plotTheGraph(stock=stock)

stock=input("Enter the Future Symbol here: ")
plotTheGraph(stock)

