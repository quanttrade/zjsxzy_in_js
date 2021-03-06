# encoding: utf-8
import numpy as np
import pandas as pd
import datetime
import os
import sys

from bokeh.io import curdoc
from bokeh.layouts import row, column, widgetbox
from bokeh.models import ColumnDataSource, NumeralTickFormatter, Range1d, LinearAxis
from bokeh.models.widgets import Slider, TextInput, TableColumn, DataTable, Select, Button, NumberFormatter
from bokeh.plotting import figure
from bokeh.palettes import Spectral9

import everyday.wind_data as wind_data
import everyday.utils as utils
import everyday.correlation as correlation
import everyday.volatility as volatility
import everyday.momentum as momentum
import everyday.mean_line as mean_line
import everyday.price as price
import everyday.const as const
import everyday.cost as cost
import everyday.industry as industry
import everyday.concentration as concentration

ASSETS_NAME = {"881001.WI": u"万得全A指数",
                "HSI.HI": u"恒生指数",
                "SPX.GI": u"标普500",
                "SX5P.GI": u"欧洲50",
                "CBA00101.CS": u"中债新综合财富指数",
                "SPGSCITR.SPI": u"商品总指数",
                "USDX.FX": u"美元指数",
                "USDCNY.FX": u"美元兑人民币",
                "AU9999.SGE": u"黄金9999",
                "B.IPE": u"WTI原油",
                "CA.LME": u"LME铜",
                "VIX.GI": u"隐含波动率指数",
                "HSCAIT.HI": u'行业龙头指数'}
DEPARTMENT_NAME = {'881001.WI': u'万得全A',
                   '000016.SH': u'上证50',
                   '000300.SH': u'沪深300',
                   '000905.SH': u'中证500',
                   '000906.SH': u'中证800',
                   '399005.SZ': u'中小板',
                   '399006.SZ': u'创业板',
                   '399550.SZ': u'央视50',
                   'HSCAIT.HI': u'恒生A股龙头',
                   '000903.SH': u'中证100',
                   '399673.SZ': u'创业板50'}
DEPARTMENT_ENG_NAME = {'881001.WI': u'wdqa',
                       '000016.SH': u'sz50',
                       '000300.SH': u'hs300',
                       '000905.SH': u'zz500',
                       '000906.SH': u'zz800',
                       '399005.SH': u'zxb',
                       '399006.SH': u'cyb'}
INDUSTRY_NAME = {'CI005001.WI': u'石油石化', 'CI005002.WI': u'煤炭', 'CI005003.WI': u'有色金属',
                 'CI005004.WI': u'电力及公用事业', 'CI005005.WI': u'钢铁', 'CI005006.WI': u'基础化工',
                 'CI005007.WI': u'建筑', 'CI005008.WI': u'建材', 'CI005009.WI': u'轻工制造',
                 'CI005010.WI': u'机械', 'CI005011.WI': u'电力设备', 'CI005012.WI': u'国防军工',
                 'CI005013.WI': u'汽车', 'CI005014.WI': u'商贸零售', 'CI005015.WI': u'餐饮旅游',
                 'CI005016.WI': u'家电', 'CI005017.WI': u'纺织服装', 'CI005018.WI': u'医药',
                 'CI005019.WI': u'食品饮料', 'CI005020.WI': u'农林牧渔', 'CI005021.WI': u'银行',
                 'CI005022.WI': u'非银行金融', 'CI005023.WI': u'房地产', 'CI005024.WI': u'交通运输',
                 'CI005025.WI': u'电子元器件', 'CI005026.WI': u'通信', 'CI005027.WI': u'计算机',
                 'CI005028.WI': u'传媒', 'CI005029.WI': u'综合'}
COLORS = Spectral9 + ["#053061", "#2166ac", "#4393c3" "#92c5de", "#d1e5f0"]# "#f7f7f7", "#fddbc7", "#f4a582", "#d6604d", "#b2182b"]
ASSETS_NAME = {key: value for key, value in ASSETS_NAME.iteritems()}
ASSETS_REV_NAME = {value: key for key, value in ASSETS_NAME.iteritems()}
# print len(COLORS)
# print len(ASSETS_NAME.values())
ASSETS_COLOR = {asset: COLORS[i] for i, asset in enumerate(ASSETS_NAME.values())}
# for key, value in ASSETS_COLOR.items():
    # print key, value
DEPARTMENT_REV_NAME = {value: key for key, value in DEPARTMENT_NAME.items()}
INDUSTRY_REV_NAME = {value: key for key, value in INDUSTRY_NAME.items()}
asset_selections = ASSETS_NAME.values()
index_selections = DEPARTMENT_NAME.values()
industry_seletions = INDUSTRY_NAME.values()
liquidity_selections = ['Amihud', 'Wu', 'Corwin and Schultz', 'Roll']
dic_key = pd.read_excel('%s/wei_index_rank.xlsx'%(const.DATA_DIR), encoding='utf-8', converters={u'代码': str})
dic_key = dic_key.set_index(u'代码')

source_price = ColumnDataSource(data=dict(date=[], close=[]))
source_sharpe = ColumnDataSource(data=dict(left=[], right=[], top=[], bottom=[], text=[], sharpe=[], color=[], text_pos=[]))
source_vol = ColumnDataSource(data=dict(days=[], vol=[], max=[], min=[], median=[], percent_75=[], percent_25=[]))
source_cor = ColumnDataSource(data=dict(days=[], cor=[], max=[], min=[], median=[], percent_75=[], percent_25=[]))
source_mom = ColumnDataSource(data=dict(date=[], mom20=[], mom60=[], mom121=[], mom242=[]))
source_turnover_cost = ColumnDataSource(data=dict(date=[], cost=[], profit=[], mean=[], zero=[], prof_mean=[], prof_50=[], rolling_mean=[], rolling_profit_mean=[]))
source_turnover_cost_text = ColumnDataSource(data=dict(text_x=[], text_y=[], text=[], prof_text_y=[], prof_text=[]))
source_consistency = ColumnDataSource(data=dict(date=[], con60=[]))
# source_liquidity = ColumnDataSource(data=dict(date=[], sz50=[], hs300=[], zz500=[], zz800=[], zxb=[], cyb=[], wdqa=[]))
source_liquidity = ColumnDataSource(data=dict(date=[], liquidity=[]))
source_liquidity_risk = ColumnDataSource(data=dict(date=[], risk=[]))
source_mean_line = ColumnDataSource(data=dict(date=[], quarter=[], year=[]))
source_turnover_days = ColumnDataSource(data=dict(date=[], tdays=[], tdays5=[], tdays10=[]))
source_concentration = ColumnDataSource(data=dict(date=[], concentration=[]))
source_volume_table = ColumnDataSource(data=dict())
source_eyby = ColumnDataSource(data=dict(date=[], spread=[], close=[]))
source_momentum = ColumnDataSource(data=dict(left=[], right=[], top=[], bottom=[], color=[], text=[], text_pos=[], momentum=[]))
source_industry_corr = ColumnDataSource(data=dict(date=[], corr=[], median=[]))
source_min_liquidity = ColumnDataSource(data=dict(date=[], liquidity=[]))
source_wei_table = ColumnDataSource(data=dict())
source_wei_index = ColumnDataSource(data=dict(date=[], val=[]))
source_record_high_table = ColumnDataSource(data=dict())
source_right_price = ColumnDataSource(data=dict(date=[], p=[]))

def update_title():
    plot_price.title.text = asset_select.value

def time2start_date(t):
    if t.find("-") != -1:
        return datetime.datetime.strptime(t, "%Y-%m-%d")
    else:
        return datetime.datetime.strptime(t, "%Y%m%d")

def update_data():
    # print("update data")
    start_date = time2start_date(time_text.value)
    end_date = time2start_date(time_end_text.value)
    symbol = ASSETS_REV_NAME[asset_select.value]

    dataframe = price.get_dataframe(symbol, start_date, end_date)
    # print dataframe.tail()
    update_title()
    if dataframe.empty:
        source_price.data = {}
    else:
        source_price.data = {'close': dataframe['close'].values, 'date': dataframe.index}
        plot_price.line('date', 'close', source=source_price, line_width=5, line_alpha=0.6, color=ASSETS_COLOR[asset_select.value])

    update_volatility()
    update_momentum()
    plot_vol.title.text = asset_select.value + u"波动率锥"
    plot_mom.title.text = asset_select.value + u"动量"

def update_momentum_statistics():
    # print('update momentum statistics')
    plot_momentum.title.text = u"计算中..."
    momM, momQ, momY = [], [], []
    yesterday = datetime.datetime.today() - datetime.timedelta(days=1)
    for asset in asset_selections:
        # print(asset)
        symbol = ASSETS_REV_NAME[asset]
        fname = '%s/%s.csv'%(const.DATA_DIR, symbol)
        if not os.path.exists(fname):
            wind_data.download_data(symbol)
        dataframe = pd.read_csv(fname)
        dataframe['date'] = pd.to_datetime(dataframe['date'], format="%Y-%m-%d")
        dataframe = dataframe.set_index('date')
        dataframe['return'] = dataframe['close'].pct_change()
        # dataframe.dropna(inplace=True)
        dataframe = dataframe[dataframe.index <= yesterday]
        momM.append(dataframe['return'][-20:].mean())
        momQ.append(dataframe['return'][-60:].mean())
        momY.append(dataframe['return'][-243:].mean())
        # print asset, dataframe['return'][-20:]
        # print asset, dataframe['return'][-20:].mean(), dataframe['return'][-60:].mean(), dataframe['return'][-243:].mean()
    df = pd.DataFrame({'momM': momM, 'momQ': momQ, 'momY': momY, 'asset': asset_selections})
    df = df.sort_values('momQ', ascending=False)
    df.to_excel('%s/temp.xlsx'%(const.DATA_DIR), index=False)

    num_asset = len(asset_selections)
    df.index = range(num_asset)
    bottom = [0 for i in range(num_asset * 3)]
    top, left, right, color, text, text_pos, momentum = [], [], [], [], [], [], []
    for i in df.index:
        # monthly momentum
        left.append(i)
        right.append(i + 0.2)
        top.append(df.loc[i]['momM'])
        color.append(COLORS[5])
        text.append(df.loc[i]['asset'])
        text_pos.append(i + 0.02)
        momentum.append('%.1f'%(df.loc[i]['momM']*10000))

        # quarterly momentum
        left.append(i + 0.25)
        right.append(i + 0.45)
        top.append(df.loc[i]['momQ'])
        color.append('#d53e4f')
        text.append('')
        text_pos.append(i + 0.27)
        momentum.append('%.1f'%(df.loc[i]['momQ']*10000))

        # yearly momentum
        left.append(i + 0.5)
        right.append(i + 0.7)
        top.append(df.loc[i]['momY'])
        color.append(COLORS[0])
        text.append('')
        text_pos.append(i + 0.52)
        momentum.append('%.1f'%(df.loc[i]['momY']*10000))
    df = pd.DataFrame({'top': top, 'bottom': bottom, 'left': left, 'right': right,
                       'text': text, 'color': color, 'text_pos': text_pos, 'momentum': momentum})
    plot_momentum.title.text = u'资产动量'
    source_momentum.data = source_momentum.from_df(df)

def update_statistics():
    # print("update statistics")
    plot_sharpe.title.text = u"计算中..."
    start_date = time2start_date(time_text.value)
    end_date = time2start_date(time_end_text.value)

    num_asset = len(asset_selections)
    bottom = [0 for i in range(num_asset)]
    top = [] # sharpe ratio
    text = asset_selections
    color = COLORS

    for asset in asset_selections:
        # print(asset)
        symbol = ASSETS_REV_NAME[asset]
        fname = "%s/%s.csv"%(const.DATA_DIR, symbol)
        if not os.path.exists(fname):
            wind_data.download_data(symbol)
        dataframe = pd.read_csv(fname)
        dataframe['date'] = pd.to_datetime(dataframe['date'], format="%Y-%m-%d")
        dataframe = dataframe.set_index('date')
        dataframe['return'] = dataframe['close'].pct_change()
        dataframe = dataframe[(dataframe.index >= start_date) & (dataframe.index <= end_date)]
        dataframe.dropna(inplace=True)
        # print dataframe.head()
        sharpe = utils.get_sharpe_ratio(dataframe['return'])
        # print sharpe
        top.append(sharpe)

    # print top
    # print bottom
    # print text
    # print color

    df = pd.DataFrame({"bottom": bottom, "top": top, "text": text,
                        "sharpe": ["%.2f"%(x) for x in top], 'color': color})
    df.sort_values('top', inplace=True, ascending=False)
    df['left'] = range(num_asset)
    df['right'] = [x+0.5 for x in df['left']]
    df['text_pos'] = [x+0.15 for x in df['left']]
    plot_sharpe.title.text = u"资产夏普率"
    source_sharpe.data = source_sharpe.from_df(df)

def update_momentum():
    # print("update momentum")
    start_date = time2start_date(time_text.value)
    end_date = time2start_date(time_end_text.value)
    symbol = ASSETS_REV_NAME[asset_select.value]

    data_df = momentum.get_dataframe(symbol, start_date, end_date)
    source_mom.data = source_mom.from_df(data_df)

def update_volatility():
    # print("update volatility")
    start_date = time2start_date(time_text.value)
    end_date = time2start_date(time_end_text.value)
    symbol = ASSETS_REV_NAME[asset_select.value]

    data_df = volatility.get_dataframe(symbol, start_date, end_date)
    if not data_df.empty:
        source_vol.data = source_vol.from_df(data_df)
        plot_vol.line(x='days', y='vol', source=source_vol, line_width=5, line_alpha=0.6, color=ASSETS_COLOR[asset_select.value])

def update_correlation():
    # print("update correlation")
    start_date = time2start_date(time_text.value)
    end_date = time2start_date(time_end_text.value)
    symbol1 = asset_text_1.value
    symbol2 = asset_text_2.value

    data_df = correlation.get_dataframe(symbol1, symbol2, start_date, end_date)
    plot_correlation.title.text = asset_text_1.value + u"与" + asset_text_2.value + u"相关性锥"
    source_cor.data = source_cor.from_df(data_df)

def update_cost(industry=False):
    # print("update cost")
    if not industry:
        index_code = DEPARTMENT_REV_NAME[department_select.value]
        name = department_select.value
    else:
        index_code = INDUSTRY_REV_NAME[industry_select.value]
        name = industry_select.value
    plot_cost.title.text = u"计算中..."
    plot_profit.title.text = u"计算中..."
    plot_turnover_days.title.text = u"计算中..."
    cost.cal_market_cost(index_code)
    plot_cost.title.text = name + u"持有成本盈亏"
    plot_profit.title.text = name + u"持仓盈亏百分比"
    plot_turnover_days.title.text = name + u'平均换手天数'
    fname = "%s/%s.xlsx"%(const.DATA_DIR, index_code)
    market_df = pd.read_excel(fname, index_col=0)
    source_turnover_days.data = {'date': market_df.index.values,
                                 'tdays': market_df['turnover days'].values,
                                 'tdays5': market_df['turnover days'].rolling(window=3).mean().values,
                                 'tdays10': market_df['turnover days'].rolling(window=7).mean().values}
    # market_df = market_df[market_df.index >= "2016-03-01"]
    market_df["mean"] = market_df["current return"].mean()
    market_df['rolling mean'] = market_df['current return'].rolling(window=242).mean()
    market_df["zero"] = 0
    market_df["prof_mean"] = market_df["profit percentage"].mean()
    market_df['rolling profit mean'] = market_df['profit percentage'].rolling(window=242).mean()
    market_df["prof_50"] = 0.5
    last_value, mean_value = market_df["current return"][-1], market_df["rolling mean"][-1]
    last_prof_value, mean_prof_value = market_df["profit percentage"][-1], market_df["rolling profit mean"][-1]
    dev_value = (last_value - mean_value) / market_df["current return"].std()
    prof_dev_value = (last_prof_value - mean_prof_value) / market_df["profit percentage"].std()
    source_turnover_cost.data = {"date": market_df.index.values,
                                 "cost": market_df["current return"].values,
                                 "mean": market_df["mean"].values,
                                 "zero": market_df["zero"].values,
                                 "rolling_mean": market_df["rolling mean"].values,
                                 "rolling_profit_mean": market_df["rolling profit mean"].values,
                                 "profit": market_df["profit percentage"].values,
                                 "prof_mean": market_df["prof_mean"].values,
                                 "prof_50": market_df["prof_50"].values}
    if last_value > mean_value:
        text_y = [mean_value + 0.04, mean_value, mean_value - 0.04]
    else:
        text_y = [last_value, last_value + 0.04, last_value - 0.04]
    if last_prof_value > mean_prof_value:
        prof_text_y = [mean_prof_value + 0.08, mean_prof_value, mean_prof_value - 0.08]
    else:
        prof_text_y = [last_prof_value, last_prof_value + 0.08, last_prof_value - 0.08]
    source_turnover_cost_text.data = {"text_x": [market_df.index[-1]]*3,
                                      "text_y": text_y,
                                      "text": [u"当前值: %.2f%%"%(last_value*100), u"历史滚动均值: %.2f%%"%(mean_value*100),
                                               u"偏离均值%.2f个标准差"%(dev_value)],
                                      "prof_text_y": prof_text_y,
                                      "prof_text": [u"当前值: %.2f%%"%(last_prof_value*100), u"历史滚动均值: %.2f%%"%(mean_prof_value*100),
                                                    u"偏离均值%.2f个标准差"%(prof_dev_value)]}

    df = utils.get_index_price(index_code, market_df.index[0], market_df.index[-1])
    source_right_price.data = source_price.from_df(df)

def update_liquidity():
    # print("update liquidity")
    # fname = '%s/liquidity.xlsx'%(const.DATA_DIR)
    symbol = liquidity_asset.value
    fname = '%s/%s.csv'%(const.DATA_DIR, symbol)
    if not os.path.exists(fname):
        wind_data.download_data(symbol)
    df = pd.read_csv(fname)
    df['date'] = pd.to_datetime(df['date'], format="%Y-%m-%d")
    df = df.set_index('date')
    df['ret'] = df['close'].pct_change()
    df['liquidity'] = df['ret'].rolling(window=121).apply(lambda x: pd.Series(x).autocorr(20))
    df = df.dropna()
    plot_liquidity.title.text = symbol + u' 流动性指标（自相关系数）：自相关系数越低，流动性越好'
    source_liquidity.data = {'date': df.index.values, 'liquidity': df['liquidity'].values}

def update_liquidity_risk():
    # print("update liquidity risk")
    fname = '%s/amihud_liquidity.xlsx'%(const.DATA_DIR)
    df = pd.read_excel(fname)
    col_name = '%s_%s'%(DEPARTMENT_ENG_NAME[DEPARTMENT_REV_NAME[index_select.value]], liquidity_select.value.lower())
    source_liquidity_risk.data = {'date': df.index,
                                  'risk': df[col_name]}

def update_min_liquidity():
    # print("update minute liquidity")
    fname = '%s/min_liquidity.xlsx'%(const.DATA_DIR)
    df = pd.read_excel(fname)
    source_min_liquidity.data = {'date': df.index, 'liquidity': df['liquidity']}

def update_mean_line():
    # print("update mean line")
    data_df = mean_line.get_dataframe()
    data_df = data_df[data_df.index >= '2016-01-01']
    source_mean_line.data = source_mean_line.from_df(data_df)

def update_industry_consistency():
    # print("update industry consistency")
    # data_df = industry.get_dataframe()
    data_df = pd.read_excel('%s/consistency.xlsx'%(const.DATA_DIR), index_col=0)
    data_df = data_df[data_df.index >= '2015-01-01']
    source_consistency.data = source_consistency.from_df(data_df)

def update_concentration():
    # print("update concentraion")
    data_df = concentration.get_dataframe()
    data_df['date'] = data_df.index
    source_concentration.data = source_concentration.from_df(data_df)

def update_volume_table():
    # print("update volume table")
    df = pd.read_excel('%s/volume.xlsx'%(const.DATA_DIR))
    source_volume_table.data = {
        'sec_name': df['sec_name'],
        'wind_code': df['wind_code'],
        'amt': df['amt'],
        'turnover': df['turnover']/100,
        'industry': df['industry'],
        'pct': df['pct_chg']/100,
    }

def update_wei_index_table():
    # print('update stock wei index table')
    df = pd.read_excel('%s/wei_index_rank.xlsx'%(const.DATA_DIR), encoding='utf-8', converters={u'代码': str})
    source_wei_table.data = {
        'code': df[u'代码'],
        'name': df[u'名称'],
        'percent': df[u'百分位'],
    }

def update_record_high_table():
    df = pd.read_excel('%s/record_high.xlsx'%(const.DATA_DIR))
    df = df.sort_values(60, ascending=False)
    source_record_high_table.data = {
        'sec_name': df['sec_name'],
        'wind_code': df['S_INFO_WINDCODE'],
        'industry': df['industry'],
        'month': df[20],
        'quarter': df[60],
        'half': df[121],
        'year': df[243],
    }

def update_eyby():
    # print("update eyby")
    df = pd.read_excel('%s/EYBY.xlsx'%(const.DATA_DIR))
    source_eyby.data = {
        'date': df.index,
        'spread': ((100 / df['pe_ttm']) - df['ytm_b']).rolling(window=5).mean(),
        'close': ((1 + df['close'].pct_change()).cumprod() - 1).rolling(window=5).mean(),
    }

def update_industry_corr():
    # print('update industry correlation')
    df = pd.read_excel('%s/industry_corr.xlsx'%(const.DATA_DIR))
    source_industry_corr.data = {
        'date': df.index,
        'corr': df['corr'].rolling(window=5).mean(),
        'median': df['median'].rolling(window=5).mean()
    }

def update_wei_index():
    # print('update wei index')
    code = wei_stock_text.value
    if code in dic_key.index:
        name = dic_key.loc[code][u'名称']
        fname = '%s/%s-%s.xlsx'%(const.SEARCH_DIR, code, name)
        df = pd.read_excel(fname)
        df = df.dropna()
        source_wei_index.data = {'date': df['day_key'], 'val': df['value']}
        plot_wei_index.title.text = name
    else:
        plot_wei_index.title.text = u'该股票微指数数据不存在'

def update_all():
    update_statistics()
    update_data()
    update_correlation()
    update_industry_consistency()
    update_cost()
    update_liquidity()
    update_liquidity_risk()
    # update_mean_line()
    update_concentration()
    update_volume_table()
    update_eyby()
    update_industry_corr()
    # update_min_liquidity()
    # update_wei_index_table()
    # update_wei_index()
    update_record_high_table()

asset_select = Select(value=u"万得全A指数", title="资产", width=300, options=asset_selections)
asset_select.on_change('value', lambda attr, old, new: update_data())
time_text = TextInput(value="2005-01-01", title="开始时间（例如：20050101或2005-01-01）", width=300)
time_text.on_change('value', lambda attr, old, new: update_all())
today = (datetime.datetime.today() - datetime.timedelta(1))
time_end_text = TextInput(value=today.strftime("%Y-%m-%d"), title="终止时间", width=300)
time_end_text.on_change('value', lambda attr, old, new: update_all())
asset_text_1 = TextInput(value="881001.WI", title=u"资产一（万得代码）", width=300)
asset_text_2 = TextInput(value="HSI.HI", title=u"资产二（万得代码）", width=300)
department_select = Select(value=u"万得全A", title=u"选择板块", width=300, options=index_selections)
department_select.on_change('value', lambda attr, old, new: update_cost())
industry_select = Select(value=u"石油石化", title=u"选择行业", width=300, options=industry_seletions)
industry_select.on_change('value', lambda attr, old, new: update_cost(industry=True))
liquidity_asset = TextInput(value='881001.WI', title=u'证券（万得代码）', width=300)
liquidity_asset.on_change('value', lambda attr, old, new: update_liquidity())
liquidity_select = Select(value='Corwin and Schultz', title=u'选择流动性风险度量', width=300, options=liquidity_selections)
liquidity_select.on_change('value', lambda attr, old, new: update_liquidity_risk())
index_select = Select(value=u'万得全A', title=u'选择指数', width=300, options=index_selections)
index_select.on_change('value', lambda attr, old, new: update_liquidity_risk())
volume_columns = [
    TableColumn(field='wind_code', title=u'证券代码'),
    TableColumn(field='sec_name', title=u'证券简称'),
    TableColumn(field='industry', title=u'证券行业'),
    TableColumn(field='amt', title=u'成交额', formatter=NumberFormatter(format='$0,0.00')),
    TableColumn(field='turnover', title=u'换手率', formatter=NumberFormatter(format='0.00%')),
    TableColumn(field='pct', title=u'涨跌幅', formatter=NumberFormatter(format='0.00%')),
]
volume_data_table = DataTable(source=source_volume_table, columns=volume_columns, width=1200)
# volume_data_table.title.text_font_size = 'Microsoft YaHei'
# volume_data_table.title = u'成交量Top50股票列表'
wei_columns = [
    TableColumn(field='code', title=u'代码'),
    TableColumn(field='name', title=u'名称'),
    TableColumn(field='percent', title=u'微指数当前百分位', formatter=NumberFormatter(format='0.00%')),
]
wei_data_table = DataTable(source=source_wei_table, columns=wei_columns, width=1200)
wei_stock_text = TextInput(value='600519', title=u'股票代码', width=300)
wei_stock_text.on_change('value', lambda attr, old, new: update_wei_index())
record_high_columns = [
    TableColumn(field='wind_code', title=u'证券代码'),
    TableColumn(field='sec_name', title=u'证券简称'),
    TableColumn(field='industry', title=u'证券行业'),
    TableColumn(field='month', title=u'一个月内创新高次数'),
    TableColumn(field='quarter', title=u'一个季度内创新高次数'),
    TableColumn(field='half', title=u'半年内创新高次数'),
    TableColumn(field='year', title=u'一年内创新高次数'),
]
record_high_data_table = DataTable(source=source_record_high_table, columns=record_high_columns, width=1200)

tools = "pan,wheel_zoom,box_select,reset"
plot_price = figure(plot_height=500, plot_width=1200, tools=tools, x_axis_type='datetime')
plot_price.title.text_font_size = "15pt"
plot_price.yaxis.minor_tick_line_color = None
plot_price.title.text_font = "Microsoft YaHei"

plot_mom = figure(plot_height=500, plot_width=1200, tools=tools, x_axis_type='datetime')
plot_mom.yaxis.formatter = NumeralTickFormatter(format="0.00%")
plot_mom.title.text_font_size = "15pt"
plot_mom.yaxis.minor_tick_line_color = None
plot_mom.title.text_font = "Microsoft YaHei"
plot_mom.line('date', 'mom20', source=source_mom, line_width=2, color='red', legend=u'一个月动量')
plot_mom.line('date', 'mom60', source=source_mom, line_width=2, color='yellow', legend=u'一个季度动量')
plot_mom.line('date', 'mom121', source=source_mom, line_width=2, color='green', legend=u'半年动量')
plot_mom.line('date', 'mom242', source=source_mom, line_width=2, color='blue', legend=u'一年动量')

plot_vol = figure(plot_height=500, plot_width=1200, tools=tools)
plot_vol.yaxis.formatter = NumeralTickFormatter(format="0.00%")
plot_vol.title.text_font_size = "15pt"
plot_vol.yaxis.minor_tick_line_color = None
plot_vol.title.text_font = "Microsoft YaHei"
plot_vol.line('days', 'max', source=source_vol, line_width=2, color='#002EB8', legend='Max')
plot_vol.line('days', 'percent_75', source=source_vol, line_width=2, color='#003DF5', legend='3/4')
plot_vol.line('days', 'median', source=source_vol, line_width=2, color='#33CCFF', legend='Median')
plot_vol.line('days', 'percent_25', source=source_vol, line_width=2, color='#33FFCC', legend='1/4')
plot_vol.line('days', 'min', source=source_vol, line_width=2, color='#33FF66', legend='Min')

plot_sharpe = figure(plot_height=500, plot_width=1200, tools=tools, x_range=[-0.5, len(asset_selections)+0.5], y_range=[-6, 10], title="资产夏普率")
plot_sharpe.quad(left='left', right='right', bottom='bottom', top='top', source=source_sharpe, color='color')
plot_sharpe.text(x='left', y=-5, text='text', source=source_sharpe, text_font_size='9pt', angle=0.5)
plot_sharpe.text(x='text_pos', y='top', text='sharpe', source=source_sharpe, text_font_size='10pt')
plot_sharpe.xaxis.visible = False
plot_sharpe.yaxis.axis_label = u"Sharpe Ratio"
plot_sharpe.title.text_font_size = "15pt"
plot_sharpe.yaxis.minor_tick_line_color = None

plot_momentum = figure(plot_height=500, plot_width=1200, tools=tools, x_range=[-0.5, len(asset_selections)], y_range=[-0.005, 0.005], title=u'资产动量')
plot_momentum.quad(left='left', right='right', bottom='bottom', top='top', source=source_momentum, color='color')
plot_momentum.text(x='left', y=-0.003, text='text', source=source_momentum, text_font_size='9pt', angle=0.5)
plot_momentum.text(x='text_pos', y='top', text='momentum', source=source_momentum, text_font_size='7pt')
plot_momentum.xaxis.visible = False
plot_momentum.title.text_font_size = '15pt'
plot_momentum.yaxis.minor_tick_line_color = None
plot_momentum.yaxis.formatter = NumeralTickFormatter(format="0.00%")

plot_correlation = figure(plot_height=500, plot_width=1200, tools=tools)
plot_correlation.yaxis.formatter = NumeralTickFormatter(format="0.00%")
plot_correlation.title.text_font_size = "15pt"
plot_correlation.yaxis.minor_tick_line_color = None
plot_correlation.title.text_font = "Microsoft YaHei"
plot_correlation.line('days', 'cor', source=source_cor, line_width=5, color='red', legend='Now')
plot_correlation.line('days', 'max', source=source_cor, line_width=2, color='#002EB8', legend='Max')
plot_correlation.line('days', 'percent_75', source=source_cor, line_width=2, color='#003DF5', legend='3/4')
plot_correlation.line('days', 'median', source=source_cor, line_width=2, color='#33CCFF', legend='Median')
plot_correlation.line('days', 'percent_25', source=source_cor, line_width=2, color='#33FFCC', legend='1/4')
plot_correlation.line('days', 'min', source=source_cor, line_width=2, color='#33FF66', legend='Min')

plot_consistency = figure(plot_height=500, plot_width=1200, tools=tools, x_axis_type='datetime')
plot_consistency.yaxis.formatter = NumeralTickFormatter(format="0.00%")
plot_consistency.title.text = u'市场方向一致度'
plot_consistency.title.text_font_size = "15pt"
plot_consistency.yaxis.minor_tick_line_color = None
plot_consistency.title.text_font = "Microsoft YaHei"
plot_consistency.line('date', 'con60', source=source_consistency, line_width=3)

plot_cost = figure(plot_height=500, plot_width=1200, tools=tools, title=u"万得全A持有成本盈亏", x_axis_type="datetime")
plot_cost.text(x='text_x', y='text_y', text='text', source=source_turnover_cost_text, text_font_size='9pt')
plot_cost.line('date', 'cost', source=source_turnover_cost, line_width=3, legend=u"当前盈亏")
plot_cost.line('date', 'rolling_mean', source=source_turnover_cost, line_width=2, color='#33FF66', legend=u"盈亏季度均值")
plot_cost.line('date', 'zero', source=source_turnover_cost, line_width=2, color=COLORS[5], legend=u"零")
plot_cost.yaxis.formatter = NumeralTickFormatter(format="0.00%")
plot_cost.yaxis.axis_label = u"percentage"
plot_cost.title.text_font_size = "15pt"
plot_cost.yaxis.minor_tick_line_color = None
plot_cost.y_range = Range1d(-0.3, 0.15)
plot_cost.extra_y_ranges = {'close': Range1d(0, 7000)}
plot_cost.add_layout(LinearAxis(y_range_name='close'), 'right')
plot_cost.line('date', 'p', source=source_right_price, y_range_name='close', line_width=2, color='#d53e4f', legend=u'指数')

plot_profit = figure(plot_height=500, plot_width=1200, tools=tools, title=u"万得全A持仓盈亏百分比", x_axis_type="datetime")
plot_profit.text(x='text_x', y='prof_text_y', text='prof_text', source=source_turnover_cost_text, text_font_size='9pt')
plot_profit.line('date', 'profit', source=source_turnover_cost, line_width=3, legend=u"当前盈亏百分比")
plot_profit.line('date', 'rolling_profit_mean', source=source_turnover_cost, line_width=2, color='#33FF66', legend=u"盈亏百分比季度均值")
plot_profit.line('date', 'prof_50', source=source_turnover_cost, line_width=2, color=COLORS[5], legend=u"50%")
plot_profit.yaxis.formatter = NumeralTickFormatter(format="0.00%")
plot_profit.yaxis.axis_label = u"percentage"
plot_profit.title.text_font_size = "15pt"
plot_profit.yaxis.minor_tick_line_color = None
plot_profit.y_range = Range1d(0, 1)
plot_profit.extra_y_ranges = {'close': Range1d(0, 7000)}
plot_profit.add_layout(LinearAxis(y_range_name='close'), 'right')
plot_profit.line('date', 'p', source=source_right_price, y_range_name='close', line_width=2, color='#d53e4f', legend=u'指数')

plot_liquidity = figure(plot_height=500, plot_width=1200, tools=tools, x_axis_type='datetime')
plot_liquidity.title.text_font_size = "15pt"
plot_liquidity.yaxis.minor_tick_line_color = None
plot_liquidity.title.text_font = "Microsoft YaHei"
plot_liquidity.title.text = u'881001.WI 流动性指标（自相关系数）：自相关系数越低，流动性越好'
plot_liquidity.line('date', 'liquidity', source=source_liquidity, line_width=2)

plot_liquidity_risk = figure(plot_height=500, plot_width=1200, tools=tools, x_axis_type='datetime')
plot_liquidity_risk.yaxis.minor_tick_line_color = None
plot_liquidity_risk.title.text_font_size = '15pt'
plot_liquidity_risk.title.text_font = 'Microsoft Yahei'
plot_liquidity_risk.title.text = u'股票流动性风险'
plot_liquidity_risk.vbar(x='date', top='risk', bottom=0, width=1, source=source_liquidity_risk)

plot_min_liquidity = figure(plot_height=500, plot_width=1200, tools=tools, x_axis_type='datetime')
plot_min_liquidity.yaxis.minor_tick_line_color = None
plot_min_liquidity.title.text_font_size = '15pt'
plot_min_liquidity.title.text_font = 'Microsoft Yahei'
plot_min_liquidity.title.text = u'沪深300分钟级股票流动性风险'
plot_min_liquidity.vbar(x='date', top='liquidity', bottom=0, width=1, source=source_min_liquidity)


'''
plot_mean_line = figure(plot_height=500, plot_width=1200, tools=tools, x_axis_type='datetime')
plot_mean_line.title.text_font_size = '15pt'
plot_mean_line.title.text_font = 'Microsoft YaHei'
plot_mean_line.title.text = u'站上均线的股票占比'
plot_mean_line.yaxis.minor_tick_line_color = None
plot_mean_line.yaxis.formatter = NumeralTickFormatter(format='0.00%')
plot_mean_line.yaxis.axis_label = u'percentage'
plot_mean_line.line('date', 'quarter', source=source_mean_line, line_width=3, color='#002EB8', legend=u'季度线')
plot_mean_line.line('date', 'year', source=source_mean_line, line_width=3, color='#33FF66', legend=u'年线')
'''

plot_turnover_days = figure(plot_height=500, plot_width=1200, tools=tools, x_axis_type='datetime')
plot_turnover_days.title.text_font_size = '15pt'
plot_turnover_days.title.text_font = 'Microsoft YaHei'
plot_turnover_days.title.text = u'万得全A平均换手天数'
plot_turnover_days.yaxis.axis_label = u'天'
plot_turnover_days.yaxis.minor_tick_line_color = None
plot_turnover_days.line('date', 'tdays', source=source_turnover_days, line_width=3, color='#002EB8')
plot_turnover_days.line('date', 'tdays5', source=source_turnover_days, line_width=1, color='green', legend=u'5天均值')
plot_turnover_days.line('date', 'tdays10', source=source_turnover_days, line_width=1, color='red', legend=u'10天均值')

plot_concentration = figure(plot_height=500, plot_width=1200, tools=tools, x_axis_type='datetime')
plot_concentration.yaxis.minor_tick_line_color = None
plot_concentration.title.text_font_size = '15pt'
plot_concentration.title.text_font = 'Microsoft Yahei'
plot_concentration.title.text = u'股票收益率集中性'
plot_concentration.vbar(x='date', top='concentration', bottom=0, width=1, source=source_concentration)

plot_eyby = figure(plot_height=500, plot_width=1200, tools=tools, x_axis_type='datetime')
plot_eyby.title.text_font_size = "15pt"
plot_eyby.yaxis.minor_tick_line_color = None
plot_eyby.title.text_font = "Microsoft YaHei"
plot_eyby.title.text = u'股债相对收益率'
plot_eyby.line('date', 'spread', source=source_eyby, line_width=2, color='red', legend=u'股债相对收益率')
plot_eyby.line('date', 'close', source=source_eyby, line_width=2, legend=u'万得全A')

plot_industry_corr = figure(plot_height=500, plot_width=1200, tools=tools, x_axis_type='datetime')
plot_industry_corr.yaxis.formatter = NumeralTickFormatter(format="0.00")
plot_industry_corr.title.text = u'行业指数相关性'
plot_industry_corr.title.text_font_size = "15pt"
plot_industry_corr.yaxis.minor_tick_line_color = None
plot_industry_corr.title.text_font = "Microsoft YaHei"
plot_industry_corr.line('date', 'corr', source=source_industry_corr, line_width=3, legend=u'均值')
plot_industry_corr.line('date', 'median', source=source_industry_corr, line_width=3, color='red', legend=u'中位数')

plot_wei_index = figure(plot_height=500, plot_width=1200, tools=tools, x_axis_type='datetime')
plot_wei_index.title.text = u'贵州茅台'
plot_wei_index.title.text_font_size = '15pt'
plot_wei_index.yaxis.minor_tick_line_color = None
plot_wei_index.title.text_font = 'Microsoft Yahei'
plot_wei_index.vbar(x='date', top='val', bottom=0, width=1, source=source_wei_index)
# plot_wei_index.line('date', 'val', source=source_wei_index, line_width=3, legend=plot_wei_index.title.text)

plot_blank = figure(plot_height=200, plot_width=1200, tools=[])

update_all()
update_momentum_statistics()

asset_text_1 = TextInput(value="881001.WI", title=u"资产一", width=300)
asset_text_2 = TextInput(value="HSI.HI", title=u"资产二", width=300)
update_button = Button(label=u"计算相关性", width=300, button_type="success")
update_button.on_click(update_correlation)
asset_row = row(asset_text_1, asset_text_2, update_button)
department_industry_row = row(department_select, industry_select)
liquidity_row = row(liquidity_select, index_select)

inputs = widgetbox(time_text, time_end_text, asset_select)

curdoc().add_root(column(inputs, plot_momentum, plot_sharpe, plot_price, plot_mom, plot_vol, asset_row, plot_correlation,
                         plot_eyby, plot_consistency, plot_industry_corr,
                         department_industry_row, plot_cost, plot_profit, plot_turnover_days,
                         liquidity_asset, plot_liquidity, liquidity_row, plot_liquidity_risk,
                         plot_concentration, volume_data_table, record_high_data_table, plot_blank))
# curdoc().add_root(column(inputs, plot_sharpe, plot_price, plot_vol, asset_row, plot_correlation))
curdoc().title = u"每日资产总结"
