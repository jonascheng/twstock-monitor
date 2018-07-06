# coding=utf-8

import logging
import plotly.plotly as py
import plotly.graph_objs as go
import plotly.tools as tools

# Scientific libraries
from numpy import arange
from scipy import stats

logger = logging.getLogger()


def linregress(y):
    xi = arange(0, len(y))
    slope, intercept, r_value, p_value, std_err = stats.linregress(xi,y)
    line = slope*xi+intercept
    print('-------------- linregress ---------------- ')
    print('slope: {:>5}'.format(slope))
    return line


def df2scatter(df):
    scatter_list = []
    for row in df:
        if row != 'date':
            scatter = go.Scatter(
                x=df['date'], # assign x as the dataframe column 'date'
                y=df[row],
                name=row
            )
            # scatter_lingress = go.Scatter(
            #     x=df['date'], # assign x as the dataframe column 'date'
            #     y=linregress(df[row]),
            #     name='{}_lingress'.format(row)
            # )
            scatter_list.append(scatter)
            # scatter_list.append(scatter_lingress)
    return scatter_list


def chart_plotting(df_list, chart_title, yaxis_label, filename):
    data = []
    for df in df_list:
        data.extend(df2scatter(df))
    layout = go.Layout(
        title=chart_title,
        yaxis=dict(
            title=yaxis_label
        )
    )
    fig = go.Figure(data=data, layout=layout)
    py.plot(fig, filename=filename)

