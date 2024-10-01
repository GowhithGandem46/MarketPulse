import streamlit as st
import sqlite3
import openai 
from streamlit_chat import message 
import re
import time 
import pandas as pd
import yfinance as yf
from alpha_vantage.fundamentaldata import FundamentalData
from stocknews import StockNews
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta

st.set_page_config(layout='wide')
hide_streamlit_style = """
                <style>
                div[data-testid="stToolbar"] {
                visibility: hidden;
                height: 0%;
                position: fixed;
                }
                div[data-testid="stDecoration"] {
                visibility: hidden;
                height: 0%;
                position: fixed;
                }
                div[data-testid="stStatusWidget"] {
                visibility: hidden;
                height: 0%;
                position: fixed;
                }
                #MainMenu {
                visibility: hidden;
                height: 0%;
                }
                header {
                visibility: hidden;
                height: 0%;
                }
                footer {
                visibility: hidden;
                height: 0%;
                }
                </style>
                """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)
# Function to validate password
def is_valid_password(password):
    # Check if the password meets the criteria
    if len(password) < 8 or not re.search("[A-Z]", password) or not re.search("[a-z]", password) or \
            not re.search("[0-9]", password) or not re.search("[!@#$%^&*(),.?\":{}|<>]", password):
        return False
    return True

# Function to create signup form with positioned image
def signup(conn, cursor):
    # Create columns for layout
    col1, col2 = st.columns([1, 1])  # Adjust the column widths as needed

    # Place image in the second column
    col2.image("b1b1_cropped.png", width=500, output_format='auto')

    # Signup form in the first column
    with col1.form(key="signup_form"):
        st.title("Sign Up")
        user_name = st.text_input("User Name", key="signup_user_name")
        user_id = st.text_input("User ID", key="signup_user_id")
        password = st.text_input("Password", type="password", key="signup_password")
        re_enter_password = st.text_input("Re-enter Password", type="password", key="signup_re_enter_password")

        if st.form_submit_button("Sign Up"):  # Update button label here
            # Check if any of the input fields are empty
            if not user_name or not user_id or not password or not re_enter_password:
                st.warning("Please enter all required data.")
            else:
                # Check if the user_id already exists in the SQLite database
                cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
                existing_user = cursor.fetchone()

                if existing_user:
                    st.error("User ID already exists. Choose a different one.")
                elif password != re_enter_password:
                    st.error("Passwords do not match.")
                elif not is_valid_password(password):
                    st.error("Password must be at least 8 characters long and contain at least one uppercase letter, one lowercase letter, one number, and one special character.")
                else:
                    # Save user data in SQLite database
                    cursor.execute("INSERT INTO users (user_name, user_id, password) VALUES (?, ?, ?)",
                                   (user_name, user_id, password))
                    conn.commit()

                    st.success("Account created successfully!")
                    st.session_state.form_submitted = True
                

# Function to create login form with positioned image
def login(conn, cursor):
    # Create columns for layout
    col1, col2 = st.columns([1, 1])  # Adjust the column widths as needed

    # Place image in the second column
    col2.image("bbb_cropped.png", width=350, output_format='auto')

    # Login form in the first column
    with col1.form(key="login_form"):
        st.title("Login")
        user_id = st.text_input("User ID", key="login_user_id")
        password = st.text_input("Password", type="password", key="login_password")

        # Check if the "Login" button is clicked
        if st.form_submit_button("Login"):  # Update button label here
            # Check if any of the input fields are empty
            if not user_id or not password:
                st.warning("Please enter all required data.")
            else:
                # Retrieve user data from SQLite database
                cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
                user_data = cursor.fetchone()

                if not user_data:
                    st.warning("Invalid User ID. Please check your User ID.")
                elif password == user_data[2].strip():  # Compare plain passwords (consider stripping whitespaces)
                    st.success("Login successful!")
                    st.session_state.form_submitted = True
                    time.sleep(2)
                else:
                    st.error("Invalid Password.")


def analyze_stock(ticker):
    try:
        # Download historical data (adjust period as needed)
        data = yf.download(ticker, period="1y")
        if data.empty:
            return None
        current_price = data["Close"].iloc[-1]
        moving_average_50 = data["Close"].rolling(window=50).mean().iloc[-1]
        moving_average_200 = data["Close"].rolling(window=200).mean().iloc[-1]
        window_size = 14
        average_gain = 0
        average_loss = 0
        for i in range(1, window_size):
            price_change = data["Close"].iloc[i] - data["Close"].iloc[i - 1]
            if price_change > 0:
                average_gain += price_change
            else:
                average_loss += abs(price_change)
        average_gain /= window_size
        average_loss /= window_size
        rsi = 100 - (100 / (1 + average_gain / average_loss))
        analysis_result = None
        if current_price > moving_average_200 and current_price > moving_average_50 and rsi < 70:
            analysis_result = "Strong Buy"
            image_to_display = "sb.png"  # Strong Buy image
        elif current_price > moving_average_50 and rsi < 50:
            analysis_result = "Buy"
            image_to_display = "b.png"  # Buy image
        elif current_price < moving_average_200 and current_price < moving_average_50 and rsi > 70:
            analysis_result = "Strong Sell"
            image_to_display = "ss.png"  # Strong Sell image
        elif current_price < moving_average_50 and rsi > 60:
            analysis_result = "Sell"
            image_to_display = "s.png"  # Sell image
        else:
            analysis_result = "Neutral"
            image_to_display = "n.png"  # Neutral image
        return analysis_result, current_price, rsi, image_to_display
    except:
        return None, None, None, None

def get_sentiment_text(sentiment_score):
            """
            This function takes a sentiment score (float) and returns a text description.
            """
            if sentiment_score == 0:
                return "Neutral"
            elif sentiment_score > 0:
                if sentiment_score < 0.5:
                    return "Positive"
                else:
                    return "Strongly Positive"
            else:
                if sentiment_score >= -0.5:
                    return "Negative"
                else:
                    return "Strongly Negative"  

def marketpulse():
    st.title('Stock Dashboard')
    # Sidebar inputs
    #logout button
    st.sidebar.markdown('<p style="margin-top: -100px;"></p>', unsafe_allow_html=True)
    if st.sidebar.button("Logout", key="logout_button", help="Click to logout and go to login page"):
        # Redirect to login page by setting the session state variables accordingly
        st.session_state.current_session = "login"
        st.session_state.form_submitted = False
    ticker = st.sidebar.text_input("Custom Ticker  (visit stocks and tickers section to find your interested stock/index's ticker)", value='TSLA', key='custom_ticker')  # Default to custom input
    stock_info = None
    try:
        stock_info = yf.Ticker(ticker).info
    except Exception:
        st.sidebar.warning(f"Enter a ticker value")
        return
    # Download stock data
    try:
        with st.spinner("Loading data..."):
            data = yf.download(ticker, period='max')
            daata = pd.read_excel('data1.xlsx')
            min_date = data.index[0]
            currency = stock_info.get('currency', 'USD')
            st.sidebar.markdown(f'<p style="font-size:30px;">Currency: {currency}</p>', unsafe_allow_html=True)
            start_date = st.sidebar.date_input('Start Date', min_value=min_date, value=datetime(2024, 1, 1))
            end_date = st.sidebar.date_input('End Date', min_value=start_date + timedelta(days=1))
            data = yf.download(ticker, start=start_date, end=end_date + timedelta(days=1))
    except Exception:
        st.sidebar.warning(f"Enter existing ticker")
        return
    selected_chart_type = st.sidebar.selectbox('Select Chart Type', ['Line Chart', 'Bar Chart', 'Candlestick Chart', "Point Chart"], index=0)

    hide_streamlit_style = """
                    <style>
                    div[data-testid="stToolbar"] {
                    visibility: hidden;
                    height: 0%;
                    position: fixed;
                    }
                    div[data-testid="stDecoration"] {
                    visibility: hidden;
                    height: 0%;
                    position: fixed;
                    }
                    div[data-testid="stStatusWidget"] {
                    visibility: hidden;
                    height: 0%;
                    position: fixed;
                    }
                    #MainMenu {
                    visibility: hidden;
                    height: 0%;
                    }
                    header {
                    visibility: hidden;
                    height: 0%;
                    }
                    footer {
                    visibility: hidden;
                    height: 0%;
                    }
                    </style>
                    """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)

    long_name = stock_info.get('longName', 'N/A')
    if 'Adj Close' not in data.columns:
        st.warning(f"No 'Adj Close' column found in the data for the selected stock/index.")
        return
    print("Data columns:", data.columns)

    # Create the selected chart based on the chart type
    fig = None
    if selected_chart_type == 'Line Chart':
        try:
            fig = px.line(data, x=data.index, y=data['Adj Close'], title=f'{long_name} - Line Chart')
        except Exception:
            st.warning(f"Error creating Line Chart: data for {ticker} doesn't exist")
            return
    elif selected_chart_type == 'Bar Chart':
        try:
            fig = px.bar(data, x=data.index, y=data['Adj Close'], title=f'{long_name} - Bar Chart')
        except Exception:
            st.warning(f"Error creating Line Chart: data for {ticker} doesn't exist")
            return
    elif selected_chart_type == 'Candlestick Chart':
        try:
            fig = go.Figure(data=[go.Candlestick(x=data.index,
                                                open=data['Open'],
                                                high=data['High'],
                                                low=data['Low'],
                                                close=data['Adj Close'])])
            fig.update_layout(title=f'{long_name} - Candlestick Chart')
        except Exception:
            st.warning(f"Error creating Line Chart: data for {ticker} doesn't exist")
            return
    elif selected_chart_type == 'Point Chart':  # Add this block for Point Chart
        try:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=data.index, y=data['Adj Close'], mode='markers', name='Point Chart'))
            fig.update_layout(title=f'{long_name} - Point Chart')
        except Exception:
            st.warning(f"Error creating Point Chart: data for {ticker} doesn't exist")
            return

    print("Fig:", fig)

    # Display the chart
    st.plotly_chart(fig)

    # Pricing Data Tab
    pricing_data, fundamental_data, news, openai1, bs_indi, sto_tick = st.tabs(["Pricing Data", "Fundamental Data", "Top 50 News", "Mpulse Bot", "Sentiment Indicator", "Stocks and Tickers"])

    with pricing_data:
        st.header('Price Movements')

        data['% Change'] = data['Adj Close'] / data['Adj Close'].shift(1) - 1
        data.dropna(inplace=True)

        # Display longName in the pricing data
        st.write(f'Stock: {long_name} ({ticker})')
        

        st.write(data)
        annual_return = data['% Change'].mean() * 252 * 100
        st.write('Annual Return is ', annual_return, '%')
        stdev = np.std(data['% Change']) * np.sqrt(252)
        st.write('Standard Deviation is ', stdev * 100, '%')
        st.write('Risk Adj. Return is ', annual_return / (stdev * 100))

        fifty_two_weeks_ago = datetime.now() - timedelta(weeks=52)
        data_52_weeks = yf.download(ticker, start=fifty_two_weeks_ago, end=datetime.now())

        seven_days_ago = datetime.now() - timedelta(days=7)
        data_7_days = yf.download(ticker, start=seven_days_ago, end=datetime.now())

        # Calculate 52-week high and low
        week52_high_date = data_52_weeks['High'].idxmax()
        week52_low_date = data_52_weeks['Low'].idxmin()
        week52_high_value = data_52_weeks.loc[week52_high_date, 'High']
        week52_low_value = data_52_weeks.loc[week52_low_date, 'Low']

    #    Calculate 7-day high and low
        week7_high_date = data_7_days['High'].idxmax()
        week7_low_date = data_7_days['Low'].idxmin()
        week7_high_value = data_7_days.loc[week7_high_date, 'High']
        week7_low_value = data_7_days.loc[week7_low_date, 'Low']

        st.write(f'52-week High Value: {week52_high_value} #-----> Date: {week52_high_date}')
        st.write(f'52-week Low Value: {week52_low_value} #----->    Date: {week52_low_date}')
        st.write(f'7-day High Value: {week7_high_value} #----->   Date: {week7_high_date}')
        st.write(f'7-day Low Value: {week7_low_value} #----->    Date: {week7_low_date}')

    # News Tab
    with news:
        st.header("Showing top 50 News...")
        sn = StockNews(ticker, save_news=False)
        df_news = sn.read_rss()

  # Check if df_news is not empty
        if not df_news.empty:
            for i in range(min(50, len(df_news))):  # Limit to 10 or the available number of news
                st.subheader(f'News {i + 1}')
      # Check if 'published', 'title', and 'summary' columns exist in df_news
                if 'published' in df_news.columns and 'title' in df_news.columns and 'summary' in df_news.columns:
                    st.write(df_news['published'][i])
                    st.write(df_news['title'][i])
                    st.write(df_news['summary'][i])

                    title_sentiment = df_news['sentiment_title'][i]
                    sentiment_text = get_sentiment_text(title_sentiment)  # Define new function
                    st.write(f'Title Sentiment: {sentiment_text}')

                    news_sentiment = df_news['sentiment_summary'][i]
                    sentiment_text = get_sentiment_text(news_sentiment)  # Reuse function
                    st.write(f'News Sentiment: {sentiment_text}')
                else:
                    st.warning('Columns are missing in the news data.')
        else:
            st.warning('No news data available for the selected stock/index.')


    with openai1:
        openai.api_key = st.secrets["api_secret"]
        model_engine = "gpt-3.5-turbo"

        def generate_response(prompt):
            completions = openai.chat.completions.create(
                model=model_engine,
                messages=[
                {"role": "user", "content": prompt}  # User message as a dictionary
                ],
                max_tokens=1024,
                n=1,
                stop=None,
                temperature=0.5,
            )
            message_text = completions.choices[0].message.content
            return message_text

        st.title("Mpulse Chatbot")

        if 'generated' not in st.session_state:
            st.session_state['generated'] = []

        if 'past' not in st.session_state:
            st.session_state['past'] = []

        def get_text():
            count = len(st.session_state.get('past', []))  # Get past message count
            new_input_text = st.text_input("You: ", key=f"new_input_{count}")  # Use dynamic key
            return new_input_text

        user_input = get_text()

        # Generate response even for the first input
        if user_input:
            output = generate_response(user_input)
            st.session_state.past.append(user_input)
            st.session_state.generated.append(output)

        # Display past conversation history
        if st.session_state['generated']:
            for i in range(len(st.session_state['generated']) - 1, -1, -1):
                message(st.session_state['past'][i], is_user=True, key=str(i) + '_user')
                message(st.session_state["generated"][i], key=str(i))


    with fundamental_data:
        key = '9FMGREG9NZI25PZW'
        fd = FundamentalData(key, output_format='pandas')
        st.subheader('Balance Sheet')
        balance_sheet = fd.get_balance_sheet_annual(ticker)[0]
        bs = balance_sheet.T[2:]
        bs.columns = list(balance_sheet.T.iloc[0])
        st.write(bs)
        st.subheader('Income Statement')
        income_statement = fd.get_income_statement_annual(ticker)[0]
        is1 = income_statement.T[2:]
        is1.columns = list(income_statement.T.iloc[0])
        st.write(is1)
        st.subheader('Cash Flow Statement')
        cash_flow = fd.get_cash_flow_annual(ticker)[0]
        cf = cash_flow.T[2:]
        cf.columns = list(cash_flow.T.iloc[0])
        st.write(cf)

    with bs_indi:
        st.title("Sentiment Indicator (Disclaimer: for educational purposes only)")
        if st.button("Analyze"):
            analysis_result, current_price, rsi, image_to_display = analyze_stock(ticker)
            if analysis_result:
                analysis_text = f"Analysis for {long_name}: {analysis_result}"
                st.markdown(f"<p style='font-size:25px;'>{analysis_text}</p>", unsafe_allow_html=True)
                # Increase the size using Markdown
                st.image(image_to_display)  # Display the corresponding image
            else:
                st.write("Error: Could not retrieve data or invalid ticker symbol.")

            st.write(
                """
                Disclaimer: This app is for educational purposes only and should not be used for actual investment decisions.
                Please consult with a financial advisor before making any investment decisions.
                """
            )
    
    with sto_tick:
        st.header('Stocks and Tickers')
        st.write(daata)
        
def main():
    st.title("MarketPulse")
    # Connect to SQLite database
    conn = sqlite3.connect("user_data.db")
    cursor = conn.cursor()

    # Apply CSS styling to move content to the left
    st.markdown("""
        <style>
            body {
                margin-right: -500px; /* Adjust the margin as needed */
            }
        </style>
    """, unsafe_allow_html=True)

    # Initialize st.session_state variables
    if "current_session" not in st.session_state:
        st.session_state.current_session = "login"

    if "form_submitted" not in st.session_state:
        st.session_state.form_submitted = False

    # Show the form based on the current session and form submitted states
    if st.session_state.form_submitted:
        if st.session_state.current_session == "signup":
            login(conn, cursor)
            if st.session_state.form_submitted:
                st.session_state.current_session = "marketpulse"
        elif st.session_state.current_session == "login":
            marketpulse()
    else:
        if st.session_state.current_session == "signup":
            signup(conn, cursor)
        elif st.session_state.current_session == "login":
            login(conn, cursor)

        # Update the toggle state and reset the form submitted state when the button is clicked
        if st.session_state.current_session != "marketpulse":
            toggle_button_label = "Login" if st.session_state.current_session == "signup" else "Sign Up"
            if st.session_state.current_session == "signup":
                col3, col4 = st.columns([1,11])
                col3.write("existing user?")
                toggle_button =  col4.button(f"{toggle_button_label}", key="toggle_button")
            else:
                col3, col4 = st.columns([1, 12])
                col3.write("New user?")
                toggle_button =  col4.button(f"{toggle_button_label}", key="toggle_button")
            
            # Update the toggle state and reset the form submitted state when the button is clicked
            if toggle_button:
                if st.session_state.current_session == "signup":
                    st.session_state.current_session = "login"
                else:
                    st.session_state.current_session = "signup"
                st.session_state.form_submitted = False

    # Close the SQLite connection
    conn.close()

# Run the main function
if __name__ == "__main__":
    main()
