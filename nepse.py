import streamlit as st
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup as BS
import requests
import urllib3
import time
import matplotlib.pyplot as plt
import plotly.express as px

def company_names():
    http = urllib3.PoolManager()
    http.addheaders = [('User-agent', 'Mozilla/61.0')]
    web_page = http.request('GET', "http://www.nepalstock.com/company?_limit=500")
    soup = BS(web_page.data, 'html5lib')
    table = soup.find('table')
    #st.write(web_page.data)
    company=[]
    rows = [row.findAll('td') for row in table.findAll('tr')[1:-2]]
    col = 0
    notfirstrun = False
    for row in rows:
        companydata =[]
        for data in row:
            if col == 5 and notfirstrun:
                companydata.append(data.a.get('href').split('/')[-1])
            else:
                companydata.append(data.text.strip())
            col += 1
        company.append(companydata)
        col =0
        notfirstrun = True

    df = pd.DataFrame(company[1:],columns=company[0])
    df.rename(columns={'Operations':'Symbol No'},inplace=True)
    df.index.name = "SN"
    df.drop(columns='',inplace=True)
    df.drop(columns='S.N.',inplace=True)
    return df
    #df.to_csv('CompanyList.csv', encoding='utf-8', index=False) 

# DATA_URL = "F:/Desktop/projects/NEPSE Streamlit APP/data/company_list.csv"

@st.cache(suppress_st_warning=True)
def load_data():
    # data = pd.read_csv(DATA_URL)
    data = company_names()
    
    lowercase = lambda x: str(x).lower()
    data.rename(lowercase, axis='columns', inplace=True)
    return data

st.subheader("View the list of Companies.")
def view_company_names():
    st.markdown("(Base URL is [http://www.nepalstock.com/company?_limit=500](http://www.nepalstock.com/company?_limit=500))")
    num = st.number_input("Enter how many records to view?", min_value=1, max_value=None, step=1)
    data_load_state = st.text('Loading data...')
    data = load_data()
    data_load_state.text("Done! (using st.cache)")
    if st.checkbox('Show raw data'):
        st.subheader('Raw data')
        st.write(data.iloc[:num])
    return data

cdf = view_company_names()

st.subheader("View Company Details.")
def view_company_details():
    symbol = st.text_input("Enter Stock Symbol. (For Reference, see above record table.)")
    symbol_no = None
    if len(symbol)>=2:
        url = "http://www.nepalstock.com/company/"
        
        try:
            req = requests.post(url, data={"stock_symbol":symbol}, verify=False)
            symbol_no = cdf[cdf["stock symbol"]==symbol]["symbol no"]
        except requests.exceptions.RequestException as e:
            print(e)

        response = req.text
        soup = BS(response, "lxml")
        table = soup.find("table")
        
        for row in table.findAll("tr")[4:]:
            col = row.findAll("td")
            st.write(col[0].string,": ",col[1].string)
        
    return symbol_no

symbol_no = view_company_details()
if  symbol_no is not None:
    symbol_no = symbol_no.tolist()[0]
# st.write(symbol_no)

st.subheader("Check Company's Progress in Years")
def CompanyStocksTransactions(SymbolNo,startDate, endDate):
    FloorSheet = []
    limit=20000
    page_no = 1   
    header = []

    while True:
        http = urllib3.PoolManager()
        http.addheaders = [('User-agent', 'Mozilla/61.0')]
        # url = "http://www.nepalstock.com.np/company/transactions/%s/%s/?startDate=%s&endDate=%s&_limit=%s"%(SymbolNo,page_no,
        url = "http://www.nepalstock.com/company/transactions/%s/%s/?startDate=%s&endDate=%s&_limit=%s"%(SymbolNo,page_no,
                                                                                                          startDate,endDate,
                                                                                                         limit)
        st.write("Current URL: ", url)

        web_page = http.request('GET',url)
        soup = BS(web_page.data, 'html5lib')
        table = soup.find('table')
        rows = [row.findAll('td') for row in table.findAll('tr')[1:-2]]
        
        print(f"Found {len(rows)} rows.")
        if len(rows)>= 1:
            if len(header)==0:
                header = [data.text.strip() for data in rows[0]]
                rows = rows[1:]
            else:
                rows=rows[1:]
            for row in rows:
                rd = [data.text.strip() for data in row]
                FloorSheet.append(rd)
            #print(rd[1])
            print("")

        else:
            break
        if len(rows)+1!=limit:
            print("Full")
            break
        else:
            page_no+=1


    # FloorSheet.insert(0, header) 
    if(len(FloorSheet) != 0):
        FloorSheetdf = pd.DataFrame(FloorSheet[1:],columns=header)
        FloorSheetdf['Date']=pd.to_datetime(FloorSheetdf['Contract No'], format='%Y%m%d%H%M%f', errors='ignore')
        
        return (1, FloorSheetdf)
    else:
        return (0, None)
@st.cache(suppress_st_warning=True)    
def view_by_year(start_date="2020-1-1", end_date="2020-1-2", symbol="2810"):
    # startDate = 2000 + year
    # startDate = str(startDate) + '-1-1'
    # endDate = 2000 + year
    # endDate = str(endDate) + '-12-31'
    st.write("From year %s to %s. Please wait few minutes."%(start_date, end_date))
    
    time1 = time.time()
    success, dftest=CompanyStocksTransactions(symbol, start_date, end_date)
    if success==1:
        st.write("Successfully scrapped data. Showing results.")
        # st.write(dftest)
    else:
        st.write("Can't scrap data. Try using another symbol. Or Another date.")
    return dftest
start_date = st.date_input("Please input start date.")
end_date = st.date_input("Please input end date.", min_value=start_date)
dfyear = view_by_year(start_date=str(start_date), end_date=str(end_date), symbol=symbol_no)
show_df = st.checkbox("Show Data")

if show_df:
    st.write(dfyear)
#st.write(dfyear.columns)
@st.cache
def load_data():
    dfyear = pd.read_csv("F:/Desktop/projects/Streamlit APP/data/NEPSE131.csv") 
    dfyear=dfyear.iloc[20000:30000]
    cl="S.N., Contract No, Stock Symbol, Buyer Broker, Seller Broker, Quantity, Rate, Amount, Date"
    ncl = cl.split(", ")
    dfyear = dfyear.rename(columns={dfyear.columns[i]:ncl[i] for i in range(len(ncl))})
    dfyear["Date"]=pd.to_datetime(dfyear["Date"])
    st.write(dfyear)
    return dfyear


date_vs_bbroker = st.checkbox("Date Vs Buyer Broker")
date_vs_sbroker = st.checkbox("Date Vs Seller Broker")
date_vs_amount = st.checkbox("Date vs Amount")
date_vs_rate = st.checkbox("Date vs Rate")


# dfyear = load_data()


def visualise_broker():
    # hist_values = np.histogram(dfyear["Date"].dt.day, bins=10, range=(0,10))[0]
    # st.bar_chart(dfyear.Date)
    # st.line_chart(dfyear[["Date", "Buyer Broker", "Seller Broker"]])
    # dfyear.hist()
    # plt.show()
    # st.pyplot()

    if date_vs_bbroker:
        st.subheader("Date Vs Buyer Broker")
        fig = px.scatter(dfyear, x="Date", y="Buyer Broker")
        st.plotly_chart(fig)

    if date_vs_amount:
        st.subheader("Date Vs Amount")
        fig = px.scatter(dfyear, x="Date", y="Amount")
        st.plotly_chart(fig)
        
    if date_vs_sbroker:
        st.subheader("Date Vs Seller Broker")
        fig = px.scatter(dfyear, x="Date", y="Seller Broker")
        st.plotly_chart(fig)
    
    if date_vs_rate:
        st.subheader("Date Vs Rate")
        fig = px.scatter(dfyear, x="Date", y="Rate")
        st.plotly_chart(fig)

visualise_broker()