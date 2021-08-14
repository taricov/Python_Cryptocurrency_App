import pandas as pd
import streamlit as st
from bs4 import BeautifulSoup
import base64
from PIL import Image
import matplotlib.pyplot as plt
import requests
import json
import time

st.set_page_config(layout="wide")
url = 'https://assets-global.website-files.com/5bc662b786ecfc12c8d29e0b/5d07c76a696bfc4b3cb88294_cryptocurrency.jpg'
im = Image.open(requests.get(url, stream=True).raw)
st.image(im, width = 1000)

st.title('CryptoCurrency Prices Web App')
st.markdown("""
In this app, The top 100 cryptocurrency prices are displayed after scraping data from the **CoinMarketCap** website!
""")
expander_bar = st.beta_expander("About")
expander_bar.markdown("""
* **Python libraries:** base64, pandas, streamlit, numpy, matplotlib, seaborn, BeautifulSoup, requests, json, time
* **Data source:** [CoinMarketCap](http://coinmarketcap.com)
""")

col1 = st.sidebar
col2, col3 = st.beta_columns((2,1))

col1.header('Input Options')
currency_price_unit = col1.selectbox('Select currency for price', ('USD', 'BTC', 'ETH'))

#scraping the data
@st.cache
def load_data():
    target = requests.get('https://coinmarketcap.com')
    soup = BeautifulSoup(target.content, 'html.parser')

    data = soup.find('script', id='__NEXT_DATA__', type='application/json')
    coins = {}
    coin_data = json.loads(data.contents[0])
    listings = coin_data['props']['initialState']['cryptocurrency']['listingLatest']['data']
    for i in listings:
      coins[str(i['id'])] = i['slug']
    
    coin_name = []
    coin_symbol = []
    market_cap = []
    percent_change_1h = []
    percent_change_24h = []
    percent_change_7d = []
    price = []
    volume_24h = []

    for i in listings:
      coin_name.append(i['slug'])
      coin_symbol.append(i['symbol'])
      price.append(i['quote'][currency_price_unit]['price'])
      percent_change_1h.append(i['quote'][currency_price_unit]['percentChange1h'])
      percent_change_24h.append(i['quote'][currency_price_unit]['percentChange24h'])
      percent_change_7d.append(i['quote'][currency_price_unit]['percentChange7d'])
      market_cap.append(i['quote'][currency_price_unit]['marketCap'])
      volume_24h.append(i['quote'][currency_price_unit]['volume24h'])

    df = pd.DataFrame(columns=['coin_name', 'coin_symbol', 'market_cap', 'percent_change_1h',
                                'percent_change_24h', 'percent_change_7d',    'price', 'volume_24h'])
    df['coin_name'] = coin_name
    df['coin_symbol'] = coin_symbol
    df['price'] = price
    df['percent_change_1h'] = percent_change_1h
    df['percent_change_24h'] = percent_change_24h
    df['percent_change_7d'] = percent_change_7d
    df['market_cap'] = market_cap
    df['volume_24h'] = volume_24h
    return df

df = load_data()

#the sidebar
sorted_coin = sorted( df['coin_symbol'] )
selected_coin = col1.multiselect('Cryptocurrency', sorted_coin, sorted_coin)

df_selected_coin = df[df['coin_symbol'].isin(selected_coin)]
num_coin = col1.slider('Display Top N Coins', 1, 100, 100)
df_coins = df_selected_coin[:num_coin]

percent_timeframe = col1.selectbox('Percent change time frame', ['7d','24h', '1h'])
percent_dict = {"7d":'percent_change_7d',"24h":'percent_change_24h',"1h":'percent_change_1h'}
selected_percent_timeframe = percent_dict[percent_timeframe]

sort_values = col1.selectbox('Sort values?', ['Yes', 'No'])

col2.subheader('Price Data of Selected Cryptocurrency')
col2.write('Data Dimension: ' + str(df_coins.shape[0]) + ' rows and ' + str(df_coins.shape[1]) + ' columns.')
col2.dataframe(df_coins)

#download CSV file
def filedownload(df):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="crypto.csv">Download CSV File</a>'
    return href

col2.markdown(filedownload(df_selected_coin), unsafe_allow_html=True)

#changing in price - table
col2.subheader('Table of % Price Change')
df_change = pd.concat([df_coins.coin_symbol, df_coins.percent_change_1h, df_coins.percent_change_24h, df_coins.percent_change_7d], axis=1)
df_change = df_change.set_index('coin_symbol')
df_change['positive_percent_change_1h'] = df_change['percent_change_1h'] > 0
df_change['positive_percent_change_24h'] = df_change['percent_change_24h'] > 0
df_change['positive_percent_change_7d'] = df_change['percent_change_7d'] > 0
col2.dataframe(df_change)

#plot
col3.subheader('Bar plot of % Price Change')
pos_selected_percent_timeframe = 'positive_' + selected_percent_timeframe

def plot():
    if percent_timeframe == percent_timeframe:
        col3.write(f'*{selected_percent_timeframe}*')
        if sort_values == 'Yes':
            df_change.sort_values(by=[selected_percent_timeframe], inplace=True)

    plt.figure(figsize=(5,25))
    plt.subplots_adjust(top = 1, bottom = 0)
    df_change[selected_percent_timeframe].plot(kind='barh', color=df_change[pos_selected_percent_timeframe].map({True: 'g', False: 'r'}))
    return col3.pyplot(plt)

plot()