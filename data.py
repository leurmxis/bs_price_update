import akshare as ak
import baostock as bs
import pandas as pd
from datetime import datetime
import pytz
import pyarrow
import time
import random

tz = pytz.timezone('Asia/Shanghai')
today = datetime.now(tz).strftime('%Y%m%d')
today = '2026-05-15'

tradeday = ak.tool_trade_date_hist_sina()
tradeday['trade_date'] = pd.to_datetime(tradeday['trade_date'])

if sum(tradeday['trade_date'] == today):
    print('trade date')
    code_df = pd.read_parquet('./list.parquet')
    bs.login()
    result = []

    for row in code_df.itertuples(index=False):
        code = row[0]
        print(code,' start')
        time.sleep(random.uniform(0.1,0.15))
        rs = bs.query_history_k_data_plus(code,
        "date,code,open,high,low,close,preclose,volume,amount,adjustflag,turn,tradestatus,pctChg,peTTM,psTTM,pcfNcfTTM,pbMRQ,isST",
        start_date=start_date, end_date=end_date,
        frequency="d", adjustflag="3")
        data_list = []
        while (rs.error_code == '0') & rs.next():
            data_list.append(rs.get_row_data())
        r = pd.DataFrame(data_list, columns=rs.fields)
        result.append(r)
    bs.logout()

    print('开始修形')
    df = pd.concat(result,ignore_index=True)
    df['股票代码'] = df['code'].str.split('.').str[1]
    cols_float = ['open','high','low','close','preclose','volume','amount','turn','pctChg','peTTM','psTTM','pcfNcfTTM','pbMRQ','adjustflag','tradestatus','isST']
    df[cols_float] = df[cols_float].replace('',np.nan)
    df[cols_float] = df[cols_float].astype('float64')
    df['日期'] = pd.to_datetime(df['date'])
    df['成交量/手'] = df['volume']/100
    df['成交额/亿'] = df['amount']/1e8
    df['流通市值/亿'] = df['volume']*df['close']/df['turn']/1e6
    name_dict = {'open':'开盘价','high':'最高价','low':'最低价','close':'收盘价','preclose':'前日收盘价除权','adjustflag':'复权状态(1后复权2前复权3不复权)','turn':'换手率','tradestatus':'交易状态','pctChg':'涨跌幅','pbMRQ':'市净率','psTTM':'市销率TTM','pcfNcfTTM':'市现率TTM'}
    df = df.rename(columns=name_dict)

    mg_df = pd.merge(df,code_df,on='股票代码',how='left')
    cols = ['日期','股票代码','简称','开盘价','最高价','最低价','收盘价','前日收盘价除权','成交量/手','成交额/亿','涨跌幅','换手率','流通市值/亿','复权状态(1后复权2前复权3不复权)','交易状态','peTTM','市销率TTM','市现率TTM','市净率','isST']
    df = mg_df[cols]
    df.to_parquet(f'./data/{today}.parquet',engine='pyarrow',index=False)
    print('写入完成')
