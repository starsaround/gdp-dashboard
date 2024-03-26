import pandas as pd
import streamlit as st
import yfinance as yf
import akshare as ak
import altair as alt

# import os
# os.environ['HTTP_PROXY'] = 'http://127.0.0.1:23333' 
# os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:23333'

def rename_cols(df):
    # 处理字段命名，以符合 Backtrader 的要求
    # 将所有列名和索引名改为小写
    df.columns = df.columns.str.lower()
    column_translation = {
    'date': 'datetime',
    'value': 'close',
    '日期': 'datetime',
    '最高': 'high',  
    '最低': 'low',              
    '开盘': 'open',
    '收盘': 'close',
    '成交量': 'volume',
    '成交额': 'turnover',
    '振幅': 'amplitude',
    '涨跌幅': 'change percent',
    '涨跌额': 'change amount',
    '换手率': 'turnover rate',
    '滚动市盈率':'pettm',
    '风险溢价': 'risk_premium'
    }

    # Rename the columns using the translation dictionary
    df.rename(columns=column_translation, inplace=True)

    if 'datetime' not in df.columns:
        df.index.name = 'datetime'
    else:
        df = df.set_index('datetime')
    return df

@st.cache_resource
def load_data():
    components = [
        'cn:600519',
        'us:AAPL',
        'hk:00700'
    ]
    return components


@st.cache_resource
def load_quotes(asset):
    market, asset = asset.split(':')
    if market=='us':
        df = yf.download(asset, back_adjust=True)
    elif market=='cn':
        df = ak.stock_zh_a_hist(asset, adjust='hfq')
    elif market=='hk':
        df = ak.stock_hk_hist(asset, adjust='hfq')
    df = rename_cols(df)
    return df


def main():
    components = load_data()
    title = st.empty()
    st.sidebar.title("设置")

    def label(symbol):
        d = {
        'cn:600519':'贵州茅台',
        'us:AAPL':'苹果',
        'hk:00700':'腾讯'
        }
        return symbol + ' - ' + d[symbol]

    # if st.sidebar.checkbox('股票列表'):
    #     st.dataframe(components[['Security',
    #                              'GICS Sector',
    #                              'Date added',
    #                              'Founded']])

    st.sidebar.subheader('选择股票')
    asset = st.sidebar.selectbox('点击',
                                 sorted(components), index=0,
                                 format_func=label)
    title.title(label(asset))
    # if st.sidebar.checkbox('View company info', True):
    #     st.table(components.loc[asset])
    data0 = load_quotes(asset)
    data = data0.copy().dropna()
    data.index.name = None

    section = st.sidebar.slider('Number of quotes', min_value=30,
                        max_value=min([2000, data.shape[0]]),
                        value=500,  step=10)

    data2 = data[-section:]['close'].to_frame('close')

    sma = st.sidebar.checkbox('SMA')
    if sma:
        period= st.sidebar.slider('SMA period', min_value=5, max_value=500,
                             value=20,  step=1)
        data[f'SMA {period}'] = data['close'].rolling(period).mean()
        data2[f'SMA {period}'] = data[f'SMA {period}'].reindex(data2.index)

    sma2 = st.sidebar.checkbox('SMA2')
    if sma2:
        period2= st.sidebar.slider('SMA2 period', min_value=5, max_value=500,
                             value=100,  step=1)
        data[f'SMA2 {period2}'] = data['close'].rolling(period2).mean()
        data2[f'SMA2 {period2}'] = data[f'SMA2 {period2}'].reindex(data2.index)

    st.subheader('图表')
    chart_data = data2/data2['close'][0]
    chart_data.index.name = 'datetime'
    chart_data = chart_data.reset_index().melt('datetime', var_name='category', value_name='y')
    
    y_min = chart_data['y'].min()
    y_max = chart_data['y'].max()
    y_scale = alt.Scale(domain=[y_min, y_max])

    c = (
        alt.Chart(chart_data)
        .mark_line(interpolate='basis')
        .encode(alt.X('datetime', title='日期'),
        alt.Y('y', title='净值',scale=y_scale),
        color='category:N').interactive()
    )

    st.altair_chart(c, use_container_width=True)
    # st.line_chart(data2/data2['close'][0])

    if st.sidebar.checkbox('统计'):
        st.subheader('基本统计值')
        st.table(data2.describe())

    if st.sidebar.checkbox('View quotes'):
        st.subheader(f'{asset} historical data')
        st.write(data2)

    st.sidebar.title("关于")
    st.sidebar.info('一个金融网页的简单示意。')

if __name__ == '__main__':
    main()
