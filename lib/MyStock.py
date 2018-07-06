# coding=utf-8

import twstock
import logging
import datetime
import requests
import pandas as pd

from twstock import Stock
from twstock import realtime
from twstock import BestFourPoint
from logging import getLogger

# Scientific libraries
from numpy import percentile

logger = logging.getLogger()


class MyAssessment(object):
    ASSESS_BUY_WHY = ['負乖離率歷史低點', '負乖離轉折往上']
    ASSESS_SELL_WHY = ['正乖離率歷史高點', '正乖離轉折往下']

    def __init__(self, stock):
        self.stock = stock

    def _bias_ratio_pivot(self, data, sample_size=3, position=False):
        sample = data[-sample_size:]

        if position is True:
            check_value = max(sample)
            pre_check_value = max(sample) > 0
        elif position is False:
            check_value = min(sample)
            # min sample and the last day should be minus
            pre_check_value = min(sample) < 0 and sample[-1] < 0

        return (pre_check_value and
                sample_size - sample.index(check_value) < sample_size and
                sample.index(check_value) != sample_size - 1)

    # 負乖離率歷史低點
    def assess_to_buy_1(self):
        br = self.stock.current_bias_ratio
        mbr = self.stock.historical_mins_bias_ratio
        check = (br <= mbr)
        logger.debug('-------------- assess_to_buy_1 {} {} ---------------- '.format(self.stock.sid, self.stock.realtime['info']['name']))
        logger.debug('bias ratio: {:.2f}'.format(br))
        logger.debug('historical minus bias ratio: {:.2f}'.format(mbr))
        logger.debug('br <= mbr: {}'.format(check))
        return check

    # 負乖離轉折往上
    def assess_to_buy_2(self):
        ndays = 3
        br = self.stock.last_N_days_bias_ratio(ndays)
        pivot = self._bias_ratio_pivot(br, sample_size=ndays, position=False)
        string = ' '.join(format(x, '.2f') for x in br)
        logger.debug('-------------- assess_to_buy_2 {} {} ---------------- '.format(self.stock.sid, self.stock.realtime['info']['name']))
        #logger.debug('last {} days bias ratio: {:.2f} {:.2f} {:.2f} {:.2f} {:.2f}'.format(ndays, *br))
        logger.debug('last {} days bias ratio: {}'.format(ndays, string))
        logger.debug('minus pivot: {}'.format(pivot))
        return pivot

    # 正乖離率歷史高點
    def assess_to_sell_1(self):
        br = self.stock.current_bias_ratio
        pbr = self.stock.historical_plus_bias_ratio
        check = (br >= pbr)
        logger.debug('-------------- assess_to_sell_1 {} {} ---------------- '.format(self.stock.sid, self.stock.realtime['info']['name']))
        logger.debug('bias ratio: {:.2f}'.format(br))
        logger.debug('historical plus bias ratio: {:.2f}'.format(pbr))
        logger.debug('br >= pbr: {}'.format(check))
        return check

    # 正乖離轉折往下
    def assess_to_sell_2(self):
        ndays = 3
        br = self.stock.last_N_days_bias_ratio(ndays)
        pivot = self._bias_ratio_pivot(br, sample_size=ndays, position=True)
        string = ' '.join(format(x, '.2f') for x in br)
        logger.debug('-------------- assess_to_sell_2 {} {} ---------------- '.format(self.stock.sid, self.stock.realtime['info']['name']))
        #logger.debug('last {} days bias ratio: {:.2f} {:.2f} {:.2f} {:.2f} {:.2f}'.format(ndays, *br))
        logger.debug('last {} days bias ratio: {}'.format(ndays, string))
        logger.debug('plus pivot: {}'.format(pivot))
        return pivot

    def assess_to_buy(self):
        result = []
        check = [self.assess_to_buy_1(), self.assess_to_buy_2()]
        if any(check):
            for index, v in enumerate(check):
                if v:
                    result.append(self.ASSESS_BUY_WHY[index])
        else:
            return False
        return ', '.join(result)

    def assess_to_sell(self):
        result = []
        check = [self.assess_to_sell_1(), self.assess_to_sell_2()]
        if any(check):
            for index, v in enumerate(check):
                if v:
                    result.append(self.ASSESS_SELL_WHY[index])
        else:
            return False
        return ', '.join(result)

    def assessment(self):
        buy = self.assess_to_buy()
        sell = self.assess_to_sell()
        if buy:
            return (True, buy)
        elif sell:
            return (False, sell)

        return None

class MyStock(Stock):
    def __init__(self, sid: str, ndays: int):
        Stock.__init__(self, sid)
        # Init data
        self.ndays = ndays
        self.realtime = realtime.get(self.sid)
        self.fetch_210()
        self.bias_ratio()

    @property
    def stock_id(self):
        return self.sid

    @property
    def stock_name(self):
        return self.realtime['info']['name']

    @property
    def historical_mins_bias_ratio(self):
        qth_percentile = 5.
        max_minus_br = percentile(self.bias_ratio[-self.ndays:], qth_percentile, interpolation='higher') 
        min_minus_br = min(self.bias_ratio[-self.ndays:])
        avg_minus_br = (max_minus_br+min_minus_br)/2
        #logger.debug('minus bias ratio : min {:.2f}, {}% percentile {:.2f}, avg {:.2f}'.format(min_minus_br, qth_percentile, max_minus_br, avg_minus_br))
        return avg_minus_br

    @property
    def historical_plus_bias_ratio(self):
        qth_percentile = 95.
        max_plus_br = max(self.bias_ratio[-self.ndays:])
        min_plus_br = percentile(self.bias_ratio[-self.ndays:], qth_percentile, interpolation='lower')
        avg_plus_br = (max_plus_br+min_plus_br)/2
        #logger.debug('plus bias ratio : max {:.2f}, {}% percentile {:.2f}, avg {:.2f}'.format(max_plus_br, qth_percentile, min_plus_br, avg_plus_br))
        return avg_plus_br

    @property
    def current_bias_ratio(self):
        return self.bias_ratio[-1]

    def last_N_days_bias_ratio(self, ndays):
        return self.bias_ratio[-ndays:]

    def fetch_210(self):
        """Fetch 210 days data"""
        today = datetime.datetime.today()
        before = today - datetime.timedelta(days=210)
        self.fetch_from(before.year, before.month)
        self.data = self.data[-180:]
        #self.data = self.data[-210:-30]
        logger.debug('-------------- Fetch {} {} ---------------- '.format(self.sid, self.realtime['info']['name']))
        logger.debug('fetch {} days of historical stock price'.format(self.ndays))
        logger.debug('date : {} {} {} {} {}'.format(*self.date[-5:]))
        logger.debug('price: {:>5} {:>5} {:>5} {:>5} {:>5}'.format(*self.price[-5:]))
        return self.data

    # N days of historical stock price
    def price_in_df(self):
        prices = {
            'date': self.date[-self.ndays:],
            'price':self.price[-self.ndays:],
        }
        return pd.DataFrame.from_dict(prices)

    def cal_N_days_ma_in_df(self, ndays_ma):
        # 計算日平均價格
        price = self.moving_average(self.price, ndays_ma)
        logger.debug('-------------- Moving Average {} {} ---------------- '.format(self.sid, self.realtime['info']['name']))
        logger.debug('calculate {} days moving average of historical stock price'.format(ndays_ma))
        logger.debug('date : {} {} {} {} {}'.format(*self.date[-5:]))
        logger.debug('price: {:>5} {:>5} {:>5} {:>5} {:>5}'.format(*price[-5:]))
        prices = {
            'date':    self.date[-self.ndays:],
            'price_ma':price[-self.ndays:],
        }
        return pd.DataFrame.from_dict(prices)

    def _cal_bias_ratio(self, data1, data2):
        min_days = min(len(data1), len(data2))
        # calculate from the latest to elder
        result = [((data1[-i]-data2[-i])/data2[-i])*100 for i in range(1, min_days + 1)]
        # return in reversed order
        return result[::-1]

    def bias_ratio(self, ndays_ma=5):
        """Calculate moving average bias ratio"""
        data1 = self.price
        data2 = self.moving_average(self.price, ndays_ma)
        self.bias_ratio = self._cal_bias_ratio(data1, data2)
        logger.debug('-------------- Bias Ratio {} {} ---------------- '.format(self.sid, self.realtime['info']['name']))
        logger.debug('calculate bias ratio of {} days moving average'.format(ndays_ma))
        logger.debug('date : {} {} {} {} {}'.format(*self.date[-5:]))
        logger.debug('ratio: {:.2f} {:.2f} {:.2f} {:.2f} {:.2f}'.format(*self.bias_ratio[-5:]))
        return self.bias_ratio

    # def cal_bias_ratio_in_df(self, days, ndays_ma1, ndays_ma2):
    #     """Calculate moving average bias ratio"""
    #     data1 = self.moving_average(self.price, ndays_ma1)
    #     data2 = self.moving_average(self.price, ndays_ma2)
    #     logger.debug('-------------- bias ratio {} {} ---------------- '.format(self.sid, self.realtime['info']['name']))
    #     logger.debug('{} days ma : {} {} {} {} {}'.format(ndays_ma1, *data1[-5:]))
    #     logger.debug('{} days ma : {} {} {} {} {}'.format(ndays_ma2, *data2[-5:]))
    #     result = self._cal_bias_ratio(data1, data2)
    #     ratio = {
    #         'date': self.date[-days:],
    #         'ratio': result[-days:],
    #     }
    #     return pd.DataFrame.from_dict(ratio)

    def bias_ratio_in_df(self):
        ratio = {
            'date': self.date[-self.ndays:],
            'ratio': self.bias_ratio[-self.ndays:],
        }
        return pd.DataFrame.from_dict(ratio)

    def assessment(self, monitor=None):
        assessment = MyAssessment(self).assessment()
        logger.debug('-------------- Assessment {} {} ---------------- '.format(self.sid, self.realtime['info']['name']))
        if assessment:
            logger.debug('{}'.format(assessment))
            if assessment[0]:
                message = 'Buy  {}'.format(assessment[1])
                logger.debug(message)
            else:
                message = 'Sell {}'.format(assessment[1])
                logger.debug(message)
            # 評估四大買賣點
            self.best_four_point()

            if monitor:
                slack_webhook = 'https://hooks.slack.com/services/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'
                data={"text": message}
                r = requests.post(slack_webhook, json=data)
        else:
            logger.debug("No action")

    def best_four_point(self):
        bfp = BestFourPoint(self).best_four_point()
        logger.debug('-------------- Best Four Point {} {} ---------------- '.format(self.sid, self.realtime['info']['name']))
        if bfp:
            logger.debug('{}'.format(bfp))
            if bfp[0]:
                logger.debug('Buy  {}'.format(bfp[1]))
            else:
                logger.debug('Sell {}'.format(bfp[1]))
        else:
            logger.debug("No action")

