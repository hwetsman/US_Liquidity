import pandas as pd
import streamlit as st
import plotly
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import requests
import fredapi as fa
st. set_page_config(layout="wide")
def Get_Fred_API_Key():
    with open('fredapikey.txt', 'r') as file:
        key = file.readline().strip()
    return key

def Get_Fred_Series(series, name):
    stem = 'https://api.stlouisfed.org/fred/series'
    fred_str = f'?series_id={series}&api_key={fred_api_key}'
    asset_series = fred.get_series(series)
    df = asset_series.to_frame()
    df.reset_index(inplace=True, drop=False)
    df.rename(columns={'index': 'Date', 0: name}, inplace=True)
    return df
col1,col2=st.columns([2,8])

blurb = 'This graphic is inspired by the definition of liquidity outlined by Dr. Jeff Ross on \
the What Bitcoin Did Podcast in July 2023. He defined it as Total Fed Assets on the balance sheet \
minus the Overnight Reverse Repo minus the Treasury General Account. These series were downloaded from \
the Fred website using the Fred API and plotted weekly. BTC price is derived from the Coinmetrics \
github repository. To eliminate a series, just click it. To isolate it, double click it. To zoom in \
just click/hold/scroll.'

col1.write(blurb)
fred_api_key = Get_Fred_API_Key()
fred = fa.Fred(api_key=fred_api_key)

series = 'RRPONTSYD'
rr_df = Get_Fred_Series(series, 'RRPONTSYD') #billions
rr_df['DATE'] = pd.to_datetime(rr_df['Date']).dt.to_period('W').dt.start_time
rr_df['RRPONTSYD'] = rr_df['RRPONTSYD'].replace('.','0')

series = 'WDTGAL'
tga_df = Get_Fred_Series(series, 'WDTGAL') #millions
tga_df['DATE'] = pd.to_datetime(tga_df['Date']).dt.to_period('W').dt.start_time

series = 'WALCL'
bal_df = Get_Fred_Series(series, 'WALCL') #millions
bal_df['DATE'] = pd.to_datetime(bal_df['Date']).dt.to_period('W').dt.start_time
liquidity_df = rr_df.merge(tga_df, on='Date',how='outer')
liquidity_df = liquidity_df.merge(bal_df, on = 'Date', how = 'outer')
liquidity_df.sort_values('Date',inplace=True)
liquidity_df = liquidity_df.dropna()
liquidity_df = liquidity_df.drop_duplicates(subset='Date', keep='first')
liquidity_df['WALCL']=liquidity_df['WALCL'].astype(float)
liquidity_df['RRPONTSYD']=liquidity_df['RRPONTSYD'].astype(float)
liquidity_df['WDTGAL']=liquidity_df['WDTGAL'].astype(float)
liquidity_df.rename(columns={'Date':'DATE'})
liquidity_df['LIQUIDITY'] = (liquidity_df['WALCL']*1000)-liquidity_df['RRPONTSYD']-(liquidity_df['WDTGAL']*1000)

print(liquidity_df)

# Import data
url = "https://raw.githubusercontent.com/coinmetrics/data/master/csv/btc.csv"
btc_df = pd.read_csv(url)
print(btc_df.tail(1000))
print(btc_df.columns)
btc_df = btc_df[['time','PriceUSD']].dropna()
btc_df.rename(columns={'time':'DATE','PriceUSD':'$BTCUSD'},inplace=True)
btc_df['DATE'] = pd.to_datetime(btc_df['DATE']).dt.to_period('W').dt.start_time
print(btc_df)
price_df = liquidity_df.merge(btc_df, on='DATE',how='inner')
print(price_df)



fig = make_subplots(specs=[[{"secondary_y": True}]], subplot_titles=(f'BTC/USD Exchange Rate and Liquidity',))
fig.add_trace(go.Scatter(x=price_df['DATE'], y=price_df['$BTCUSD'], name='$BTCUSD'), secondary_y=False)
fig.add_trace(go.Scatter(x=price_df['DATE'], y=price_df['LIQUIDITY'], name='Liquidity(BAL-TGA-RR)'), secondary_y=True)
fig.add_trace(go.Scatter(x=price_df['DATE'], y=price_df['WALCL'], name='Fed Balance Sheet'), secondary_y=True)
fig.add_trace(go.Scatter(x=price_df['DATE'], y=price_df['RRPONTSYD'], name='Over Night RR'), secondary_y=True)
fig.add_trace(go.Scatter(x=price_df['DATE'], y=price_df['WDTGAL'], name='Treasury Global Acct'), secondary_y=True)


fig.update_yaxes(type='log', tickformat='$,.0f', secondary_y=False)
fig.update_yaxes(type='log', tickformat='$,.0f', secondary_y=True)
fig.update_layout(showlegend=True, width=1100, height=700)
col2.plotly_chart(fig)
