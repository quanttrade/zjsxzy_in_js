# encoding: utf-8

import pandas as pd
import datetime
import empyrical
import os

import const

DATA_DIR = "D:/sheet/zhiyingtianyi portfolio"
ZHIYING_FILE = "%s/zhiyingtianyi No.1.csv"%(DATA_DIR)

def merge_to_sheet(date):
    fname = "%s/%s.csv"%(DATA_DIR, date)
    if not os.path.exists(fname):
        print fname
        print("file not exist")
        return

    today_df = pd.read_csv(fname)
    today_info = today_df.iloc[0]
    today_info.index = today_info.index.map(lambda x: int(x))
    date = pd.to_datetime(date, format="%Y-%m-%d")
    zhiying_df = pd.read_csv(ZHIYING_FILE)
    zhiying_df.index = pd.to_datetime(zhiying_df['date'], format="%Y/%m/%d")
    zhiying_df.loc[date] = [date.strftime("%Y/%m/%d")] + today_info[today_info.index < 24].tolist()
    # print zhiying_df.dropna().tail()
    zhiying_df.to_csv(ZHIYING_FILE, index=False)

    # 24期之后
    zhiying_df = pd.read_excel(const.ZHIYING_FILE2, index_col=0)
    zhiying_df.loc[date] = today_info[today_info.index >= 24].tolist()
    # print zhiying_df.dropna().tail()
    zhiying_df.to_excel(ZHIYING_FILE2)

def get_statistics(date):
    end_date = datetime.datetime.strptime(date, "%Y-%m-%d")
    portfolio_name, net_value, year_return, annual_return, total_return, max_drawdown, sharpe, volatility = [], [], [], [], [], [], [], []

    zhiying_df = pd.read_csv(const.ZHIYING_FILE)
    zhiying_df.index = pd.to_datetime(zhiying_df['date'], format='%Y/%m/%d')
    zhiying_df = zhiying_df[zhiying_df.index <= end_date]
    if zhiying_df.shape[0] == 0:
        return
    assets = assets = [unicode(x) for x in range(const.first_num_of_portfolio, const.last_num_of_portfolio+1) \
                       if ((x not in const.exceptions) and (x < 24))]

    for asset in assets:
        df = zhiying_df[[asset]]
        df = df.dropna()
        df.loc[:, 'return'] = df.pct_change()
        df.loc[:, 'net value'] = (1+df['return']).cumprod()
        df.loc[df.index[0], 'net value'] = 1

        if df.index[-1] < end_date:
            return

        portfolio_name.append(u"智盈添易一号第%s期"%(asset))
        net_value.append(df.loc[df.index[-1], 'net value'])
        total_return.append(df.loc[df.index[-1], 'net value'] - 1)
        annual_return.append(empyrical.annual_return(df['return'].dropna()))
        max_drawdown.append(empyrical.max_drawdown(df['return'].dropna()))
        sharpe.append(empyrical.sharpe_ratio(df['return'].dropna()))
        volatility.append(empyrical.annual_volatility(df['return'].dropna()))
        df = df[df.index >= datetime.datetime(2018, 1, 1)]
        start_value = df.loc[df.index[0], 'net value']
        end_value = df.loc[df.index[-1], 'net value']
        year_return.append((end_value-start_value)/start_value)

    # 24期之后
    assets = assets = [x for x in range(const.first_num_of_portfolio, const.last_num_of_portfolio+1) \
                       if ((x not in const.exceptions) and (x >= 24))]

    zhiying_df = pd.read_excel(const.ZHIYING_FILE2, index_col=0)
    zhiying_df = zhiying_df[zhiying_df.index <= end_date]
    if zhiying_df.shape[0] == 0:
        return
    for asset in assets:
        df = zhiying_df[[asset]]
        df = df.dropna()
        df.loc[:, 'return'] = df[asset] / 100.
        df.loc[:, 'net value'] = (1+df['return']).cumprod()
        df.loc[df.index[0], 'net value'] = 1

        portfolio_name.append(u"智盈添易一号第%s期"%(asset))
        net_value.append(df.loc[df.index[-1], 'net value'])
        total_return.append(df.loc[df.index[-1], 'net value'] - 1)
        annual_return.append(empyrical.annual_return(df['return'].dropna()))
        max_drawdown.append(empyrical.max_drawdown(df['return'].dropna()))
        sharpe.append(empyrical.sharpe_ratio(df['return'].dropna()))
        volatility.append(empyrical.annual_volatility(df['return'].dropna()))
        df = df[df.index >= datetime.datetime(2018, 1, 1)]
        start_value = df.loc[df.index[0], 'net value']
        end_value = df.loc[df.index[-1], 'net value']
        year_return.append((end_value-start_value)/start_value)

    ret = {u'组合': portfolio_name,
           u'单位净值': net_value,
           u'今年以来业绩': year_return,
           u'成立以来业绩': total_return,
           u'年化收益率': annual_return,
           u'最大回撤': max_drawdown,
           u'夏普率': sharpe,
           u'波动率': volatility
    }

    df = pd.DataFrame(ret)
    df = df[[u"组合", u'单位净值', u'今年以来业绩', u'成立以来业绩', u'年化收益率', u'最大回撤', u'夏普率', u'波动率']]
    df.loc[:, u'单位净值'] = df[u'单位净值'].map(lambda x: "%.4f"%x)
    df.loc[:, u'今年以来业绩'] = df[u'今年以来业绩'].map(lambda x: "%.2f%%"%(x*100))
    df.loc[:, u"成立以来业绩"] = df[u"成立以来业绩"].map(lambda x: "%.2f%%"%(x*100))
    df.loc[:, u"年化收益率"] = df[u"年化收益率"].map(lambda x: "%.2f%%"%(x*100))
    df.loc[:, u"最大回撤"] = df[u"最大回撤"].map(lambda x: "%.2f%%"%(-x*100))
    df.loc[:, u"夏普率"] = df[u"夏普率"].map(lambda x: "%.2f"%x)
    df.loc[:, u"波动率"] = df[u"波动率"].map(lambda x: "%.2f%%"%(x*100))
    writer = pd.ExcelWriter('%s/%s.xlsx'%(DATA_DIR, date))
    df.to_excel(writer, index=False)
    writer.save()
    df = pd.read_excel('%s/%s.xlsx'%(DATA_DIR, date))

if __name__ == "__main__":
    merge_to_sheet("2017-11-03")
    # get_statistics("2017-11-02")
