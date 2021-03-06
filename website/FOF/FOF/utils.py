# encoding: utf-8

import empyrical
from WindPy import w
import pandas as pd
import datetime
import calendar
import os

import const
import stock_fund
import bond_fund
import mixed_fund

def wind2df(raw_data):
    dic = {}
    for data, field in zip(raw_data.Data, raw_data.Fields):
        dic[str(field.lower())] = data
    if len(raw_data.Times) == len(dic[dic.keys()[0]]):
        return pd.DataFrame(dic, index=raw_data.Times)
    else:
        return pd.DataFrame(dic)

def get_statistics(ticker, end_date, k):
    """
    得到一只基金在end_date前推k个交易日的
    1. 收益率
    2. 波动率
    3. 最大回撤
    4. Sharpe
    5. Calmar
    """
    fname = '%s/history/%s.xlsx'%(const.DATA_DIR, ticker)
    df = pd.read_excel(fname, index_col=0)
    df = df[df.index <= end_date]
    if k > df.shape[0]:
        return 0, 0, 0, 0, 0

    df = df[df.index >= df.index[-k]]
    df.loc[:, 'return'] = df.loc[:, 'nav_adj'].pct_change()
    returns = (df.ix[-1, 'nav_adj'] - df.ix[0, 'nav_adj']) / df.ix[0, 'nav_adj']
    volatility = empyrical.annual_volatility(df['return'])
    max_drawdown = empyrical.max_drawdown(df['return'])
    sharpe = empyrical.sharpe_ratio(df['return'])
    calmar = empyrical.calmar_ratio(df['return'])
    return returns, volatility, max_drawdown, sharpe, calmar

def get_historical_return(df):
    df['3-year return'] = df['nav_adj'].pct_change(729)
    df['2-year return'] = df['nav_adj'].pct_change(486)
    df['1-year return'] = df['nav_adj'].pct_change(243)
    df['6-month return'] = df['nav_adj'].pct_change(121)
    df['3-month return'] = df['nav_adj'].pct_change(60)
    df['1-month return'] = df['nav_adj'].pct_change(20)
    return df

def get_all_historical_return(ticker_list):
    for ticker in ticker_list:
        print ticker
        fname = '%s/history/%s.xlsx'%(const.DATA_DIR, ticker)
        if not os.path.exists(fname):
            down_historical_nav(ticker)
        df = pd.read_excel(fname, index_col=0)
        df = get_historical_return(df)
        df.to_excel(fname)

def down_historical_nav(ticker):
    """
    下载基金历史净值并保存
    """

    w.start()
    end_date = datetime.datetime.today() - datetime.timedelta(1)
    end_date = end_date.strftime('%Y-%m-%d')
    data = w.wss(ticker, "issue_date")
    start_date = data.Data[0][0]
    if start_date < pd.to_datetime('2010-01-01', format='%Y-%m-%d'):
        start_date = pd.to_datetime('2010-01-01', format='%Y-%m-%d')
    days = (pd.to_datetime(end_date, format='%Y-%m-%d') - start_date).days
    data = w.wsd(ticker, "NAV_adj", "ED-%dD"%(days), end_date, "")
    df = wind2df(data)
    df.index = pd.to_datetime(df.index)
    df = df[df.index >= '2010-01-01']
    df.to_excel('%s/history/%s.xlsx'%(const.DATA_DIR, ticker))

def calculate_empyrical(fund_type):
    filename = '%s/%s_return.pkl'%(const.FOF_DIR, fund_type)
    ret_df = pd.read_pickle(filename)
    # Omega Ratio
    df = pd.DataFrame(index=ret_df.columns)
    df.loc[:, 'omega'] = ret_df.apply(lambda x: empyrical.omega_ratio(x))

    fname = '%s/%s_empyrical.xlsx'%(const.FOF_DIR, fund_type)
    df.to_excel(fname)

def download_season_rpt(ticker, rptdates):
    '''
    返回基金季度报告数据
    '''
    w.start()
    columns = "prt_netasset,prt_stocktonav,prt_bondtonav,prt_cashtonav,prt_stocktoasset"
    print('downloading %s season report'%(ticker))
    df = pd.DataFrame({}, index=rptdates, columns=columns.split(','))
    for rptdate in rptdates:
        data = w.wss(ticker, columns, 'rptDate=%s'%(rptdate.strftime('%Y-%m-%d')))
        data = [val[0] for val in data.Data]
        df.loc[rptdate] = data
    fname = '%s/%s.xlsx'%(const.RPT_DIR, ticker)
    # df.to_excel(fname)
    df = df.dropna(how='all')
    return df

def generate_rptdate(start_date):
    """
    生成报告期
    """
    start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
    years = range(2000, 2019)
    months = [3, 6, 9, 12]
    rptdates = []
    today = datetime.datetime.today()
    for year in years:
        for month in months:
            day = calendar.monthrange(year, month)[1]
            if datetime.datetime(year, month, day) < start_date:
                continue
            if datetime.datetime(year, month, day) > pd.to_datetime(const.rptDate):
                break
            rptdates.append('%d-%02d-%02d'%(year, month, day))
    return rptdates

def get_all_funds():
    stock_df = pd.read_excel(const.stock_funds_file)
    mixed_df = pd.read_excel(const.mixed_funds_file)
    bond_df = pd.read_excel(const.bond_funds_files)
    all_df = stock_df.append(mixed_df).append(bond_df)
    return all_df
