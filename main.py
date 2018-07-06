#!/usr/bin/env python
# coding=utf-8
#
import click
import logging
import click_log

from datetime import date

from lib.MyStock import MyStock
from lib.util import chart_plotting

logger = logging.getLogger()
click_log.basic_config(logger)


@click.command()
@click.option('--sid', type=click.STRING, 
                prompt='stock id', help='the stock id to query. Ex: 2337')
@click.option('--days', type=click.IntRange(min=5, max=60, clamp=False),
                prompt='last N days', help='the last N days to calculate.')
@click.option('--ma', type=click.IntRange(min=3, max=30, clamp=False),
                prompt='M days moving average', help='the M days moving average to calculate.')
@click.option('--plot/--no-plot', default=False,
                prompt='chart plotting', help='chart plotting?')
@click.option('--monitor/--no-monitor', default=False,
                prompt='stock monitoring', help='stock monitoring?')
@click_log.simple_verbosity_option(logger)
def main(sid, days, ma, plot, monitor):
    s = MyStock(sid, days)

    # N日收盤價
    df = s.price_in_df()
    # if plot:
    #     chart_title = '{} ({}) {}日收盤價'.format(s.stock_id, s.stock_name, days)
    #     yaxis_label = 'Price'
    #     filename = '{}_price_{}'.format(s.stock_id, date.today())
    #     chart_plotting([df], chart_title, yaxis_label, filename)
    # print(df)

    # N日均線
    df2 = s.cal_N_days_ma_in_df(ma)
    if plot:
        chart_title = '{} ({}) {}日均線'.format(s.stock_id, s.stock_name, ma)
        yaxis_label = 'Moving Average'
        filename = '{}_ma_{}'.format(s.stock_id, date.today())
        chart_plotting([df, df2], chart_title, yaxis_label, filename)
    # print(df2)

    # data1 = s.cal_bias_ratio_in_df(days, 1, 5)
    # print(data1)
    
    # N日乖離率
    df3 = s.bias_ratio_in_df()
    if plot:
        chart_title = '{} ({}) {}日乖離率'.format(s.stock_id, s.stock_name, ma)
        yaxis_label = 'Bias Ratio'
        filename = '{}_bias_ratio_{}'.format(s.stock_id, date.today())
        chart_plotting([df3], chart_title, yaxis_label, filename)
    #print(df3)
    
    # 我的評估
    s.assessment(monitor)

if __name__ == '__main__':
    main()
