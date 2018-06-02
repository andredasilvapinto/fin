from datetime import datetime

import fix_yahoo_finance as yf
import matplotlib.pyplot as plt
import math
import numpy as np
import pandas as pd
import pandas_datareader as pdr
from dateutil.relativedelta import relativedelta
from collections import defaultdict

DAILY_RET = 'daily_ret'
YESTERDAY_ADJ_CLOSE = 'yesterday_adj_close'
ADJUSTED_CLOSE = 'Adj Close'

yf.pdr_override()

symb = {
    #    'SPY': {'name': 'S&P 500 (Ref)', 'cost': 0.1, 'w': 0.73},
    #    'IVV': {'name': 'iShares Core S&P 500 USD (Dist)', 'cost': 0.07, 'w': 0.27}
    'CSPX.AS': {'name': 'iShares Core S&P 500 (Acc)', 'cost': 0.07, 'w': 0.20},
    'CEMU.AS': {'name': 'iShares MSCI EMU (Acc)', 'cost': 0.33, 'w': 0},
    'IMAE.AS': {'name': 'iShares MSCI Europe (Acc)', 'cost': 0.33, 'w': 0},
    'MEUD.PA': {'name': 'Lyxor Stoxx Europe 600 (Acc)', 'cost': 0.07, 'w': 0.20},
    #    'ERO.PA': {'name': 'SPDR MSCI Europe (Acc)', 'cost': 0.18},
    #    'XMME.DE': {'name': 'Xtrackers MSCI Emerging Markets (Acc)', 'cost': 0.20},
    #    'EMIM.AS': {'name': 'iShares Core MSCI Emerging Markets IMI (Acc)', 'cost': 0.25},
    #    'AEME.PA': {'name': 'Amundi ETF MSCI Emerging Markets UCITS ETF DR (Acc)', 'cost': 0.20},
    #    'IEMA.AS': {'name': 'iShares MSCI Emerging Markets (Acc)', 'cost': 0.68},
    'IWDA.AS': {'name': 'iShares Core MSCI World (Acc)', 'cost': 0.20, 'w': 0.50},
    #    'DBXH.DE': {'name': 'X II Global Infl-Lnkd Bd 1C Hedge (Acc)', 'cost': 0.25, 'w': 0.99},
    #    'DBZB.DE': {'name': 'Xtrackers Global Sovereign Hedge (Acc)', 'cost': 0.25, 'w': 0.01},
    #    'IUSN.DE': {'name': 'iShares MSCI World Small Cap (Acc)', 'cost': 0.35, 'w': 0.01},
    'ZPRS.DE': {'name': 'SPDR MSCI World Small Cap (Acc)', 'cost': 0.45, 'w': 0.10},
}


def get_dt_value(item):
    return item.index.date[0], item.values[0]


def weighted_return(w):
    return lambda r: w * (r[ADJUSTED_CLOSE] - r[YESTERDAY_ADJ_CLOSE]) / r[YESTERDAY_ADJ_CLOSE]


def annualized_log_ret(series):
    ln_ret_series = pd.Series(series.apply(lambda ret: math.log(1 + ret), 1))
    ln_ret_std_dev_d = ln_ret_series.std()
    return ln_ret_std_dev_d * math.sqrt(252)


def annualize(first, last, years):
    return (last / first) ** (1 / years) - 1


delta_years = 3
# end = datetime.now()
end = datetime(year=2018, month=1, day=1)
start = end - relativedelta(years=delta_years)

data_set = []
w_ret = pd.DataFrame([])
portfolio = defaultdict(float)

for ticker, meta in symb.items():
    name = meta['name']
    cost = meta['cost']
    weight = meta['w']
    print('Loading {}... '.format(name), end='')

    data = pdr.get_data_yahoo(symbols=ticker, start=start, end=end)
    print('DONE - {} rows'.format(len(data)))

    data[YESTERDAY_ADJ_CLOSE] = data[ADJUSTED_CLOSE].shift(1)

    data[DAILY_RET] = data.apply(weighted_return(1), 1)

    first_dt, first_value = get_dt_value(data.head(1)[ADJUSTED_CLOSE])
    last_dt, last_value = get_dt_value(data.tail(1)[ADJUSTED_CLOSE])

    return_pct = (last_value - first_value) / first_value * 100
    return_pct_y = annualize(first_value, last_value, delta_years) * 100
    ln_ret_std_dev_y = annualized_log_ret(data[DAILY_RET]) * 100

    portfolio['ret'] += weight * return_pct
    portfolio['cost'] += weight * cost
    w_ret[ticker] = data.apply(weighted_return(weight), 1)

    data_set.append([ticker, name, weight, first_dt, last_dt, first_value, last_value,
                     return_pct, return_pct_y, ln_ret_std_dev_y, cost])

w_ret = w_ret.sum(axis=1)
w_ret_std_dev_y = annualized_log_ret(w_ret) * 100
last = 100 + portfolio['ret']
annualized_portfolio_ret = annualize(100, last, delta_years) * 100

data_set.append(['ALL', 'Portfolio', 1, start, end, 100, last,
                 portfolio['ret'], annualized_portfolio_ret, w_ret_std_dev_y, portfolio['cost']])

df = pd.DataFrame(data_set, columns=['ticker', 'name', 'weight', 'first day', 'last day', 'first value', 'last value',
                                     'return %', 'return % y', 'ln std dev % y', 'cost'])

print(df.to_string())

fig, ax = plt.subplots()
# ax.set_xlim(0, 12)
# ax.set_ylim(0, 11)
grouped = df.groupby('name')

for key, group in grouped:
    group.plot(ax=ax, kind='scatter', x='ln std dev % y', y='return % y',
               label=key, color=np.random.random(3), s=(100 * group['cost']) ** 1.5)

plt.show()
