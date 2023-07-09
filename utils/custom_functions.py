import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np
import base64
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from utils.sql_functions import *
from unidecode import unidecode
import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from pandas.api.types import (
    is_categorical_dtype,
    is_datetime64_any_dtype,
    is_numeric_dtype,
    is_object_dtype,
)

def multi(x, y):
    number = x * y
    return number

def filter_dataframe(df):
    """
    Adds a UI on top of a dataframe to let viewers filter columns

    Args:
        df (pd.DataFrame): Original dataframe

    Returns:
        pd.DataFrame: Filtered dataframe
    """
    modify = st.checkbox("Add filters", value=True)

    if not modify:
        return df

    df = df.copy()

    # Try to convert datetimes into a standard format (datetime, no timezone)
    for col in df.columns:
        if is_object_dtype(df[col]):
            try:
                df[col] = pd.to_datetime(df[col])
            except Exception:
                pass

        if is_datetime64_any_dtype(df[col]):
            df[col] = df[col].dt.tz_localize(None)

    modification_container = st.container()

    with modification_container:
        to_filter_columns = st.multiselect(label="Filter dataframe on", options=df.columns)
        for column in to_filter_columns:
            left, right = st.columns((1, 20))
            # Treat columns with < 10 unique values as categorical
            if is_categorical_dtype(df[column]) or df[column].nunique() < 10:
                user_cat_input = right.multiselect(
                    f"Values for {column}",
                    df[column].unique(),
                    default=list(df[column].unique()),
                )
                df = df[df[column].isin(user_cat_input)]
            elif is_numeric_dtype(df[column]):
                _min = float(df[column].min())
                _max = float(df[column].max())
                step = (_max - _min) / 100
                user_num_input = right.slider(
                    f"Values for {column}",
                    min_value=_min,
                    max_value=_max,
                    value=(_min, _max),
                    step=1.00,
                )
                df = df[df[column].between(*user_num_input)]
            elif is_datetime64_any_dtype(df[column]):
                user_date_input = right.date_input(
                    f"Values for {column}",
                    value=(
                        df[column].min(),
                        df[column].max(),
                    ),
                )
                if len(user_date_input) == 2:
                    user_date_input = tuple(map(pd.to_datetime, user_date_input))
                    start_date, end_date = user_date_input
                    df = df.loc[df[column].between(start_date, end_date)]
            else:
                user_text_input = right.text_input(
                    f"Substring or regex in {column}",
                )
                if user_text_input:
                    df = df[df[column].astype(str).str.contains(user_text_input)]
    
    df.insert(0, 'select', [False]* len(df.index))
    df_selected = st.experimental_data_editor(df, num_rows="fixed")

    return df_selected

def convert_df(df):
    return df.to_csv().encode('utf-8')

def create_barplot_using_column(df, column, top_n=None, xaxis_title=None, show_percent = False, color = False, show_values = False):
    
    df_plot = df.copy()

    df_plot[column] = df_plot[column].astype(str)
    df_plot[column] = np.where(df_plot[column] == 'nan', '-1', df_plot[column])
    df_plot[column] = np.where(df_plot[column] == 'None', '-1', df_plot[column])

    # Get value counts for the column
    value_counts = df_plot[column].astype('str').value_counts()

    if top_n is not None:
        # Get the top N categories
        value_counts = value_counts.head(top_n)

    # Create a dataframe from the value counts
    df_counts = pd.DataFrame({'Category': value_counts.index, 'Count': value_counts.values})
    df_counts['Category'] = df_counts['Category'].astype(str)

    if show_percent:
        # Calculate percentage for each category
        total_count = df_counts['Count'].sum()
        df_counts['Percent'] = df_counts['Count'] / total_count * 100

        # Update y-axis title to show percentage
        yaxis_title = '%'
        y_col = 'Percent'
    else:
        # Update y-axis title to show count
        yaxis_title = 'Count'
        y_col = 'Count'

    if color:
        # Create a bar plot using plotly express
        fig = px.bar(df_counts, x='Category', y=y_col, color='Category', text_auto = '.3s')
    else:
        fig = px.bar(df_counts, x='Category', y=y_col, text_auto = '.3s')
    
    if xaxis_title is not None:
        fig.update_layout(xaxis_title=xaxis_title)
        fig.update_layout(yaxis_title=yaxis_title)
    
    st.plotly_chart(fig, use_container_width=True)
    if show_values:
        st.download_button(label=f'Download {column} data as CSV', data=convert_df(df_counts),
                           file_name=f'df_counts{column}.csv', mime='text/csv')
    


def create_histogram_using_column(df, column, nbins=10, histfunction = 'count'):

    fig = px.histogram(df, x=column, nbins=nbins, histfunc=histfunction)

    return st.plotly_chart(fig, use_container_width=True)

def format_data_washing_complex_data(df_input, afa = 1.27, add_historical_data = True):

    df_new = df_input.copy()

    try:
        df_new['b2b_b2c_limo'] = np.where(df_new['b2b_b2c_limo'] == 1, 'b2b', 'b2c')
    except:
        pass

    try:
        #convert some columns to date and not datetime
        df_new['wash_date'] = pd.to_datetime(df_new['wash_date'])
        df_new['wash_date_day'] = pd.to_datetime(df_new['wash_date_day']).dt.date
        df_new['wash_date_week'] = pd.to_datetime(df_new['wash_date_week']).dt.date
        df_new['wash_date_month'] = pd.to_datetime(df_new['wash_date_month']).dt.date
        df_new['wash_date_quarter'] = pd.to_datetime(df_new['wash_date_quarter']).dt.date
    except:
        pass

    if add_historical_data:
        washes_hist = sql_query("SELECT * FROM cleango.bi_past_transaction_formated")
        washes_hist['wash_date'] = pd.to_datetime(washes_hist['wash_date'])
        washes_hist['wash_date_day'] = pd.to_datetime(washes_hist['wash_date_day']).dt.date
        washes_hist['wash_date_week'] = pd.to_datetime(washes_hist['wash_date_week']).dt.date
        washes_hist['wash_date_month'] = pd.to_datetime(washes_hist['wash_date_month']).dt.date
        washes_hist['wash_date_quarter'] = pd.to_datetime(washes_hist['wash_date_quarter']).dt.date

        df_only_b2c = df_new[((df_new['b2b_b2c_limo'].isin(['b2c'])) | (df_new['wash_date'] >= '2023-03-19'))].copy()
        
        # concat washes_hist with df
        df_all = pd.concat([df_only_b2c, washes_hist], ignore_index=True)
        df = df_all.copy()
       
    else:
        df = df_new.copy()

    try:
        df['price'] = np.where(((df['b2b_b2c_limo'].isin(['Limo', 'b2b']) & (df['price'] <= 0 ))), df['base_wash_price'], df['price'])
    except:
        pass

    try:
        df['price'] = np.where((df['price']) < (df['original_price'] + 3500), df['original_price'], df['price'])
    except:
        pass

    try:
        df['price'] = np.where(df['b2b_b2c_limo'].isin(['b2c']), (df['price'] / afa), (df['price']))
    except:
        pass
    
    try:
        df['zip_code'] = df['zip_code'].astype(str)
    except:
        pass
    
    try:
        df['zip_code'] = np.where(df['zip_code'] == 'None',
                                df['street'].str.extract(r'(\d{4})', expand=False),
                                df['zip_code'].astype(str))
    except:
        pass

    try:
        df['district'] = df['zip_code'].apply(lambda x: x[1:3] if isinstance(x, str) and x.startswith('1') and len(x) == 4 else np.nan)
    except:
        pass

    try:
        df['margin'] = df['price'] - df['total_commision_price']
    except:
        pass

    try:
        df['profit_ratio'] = (df['margin'] / df['price'])
    except:
        pass

    try:
        # convert wash_date which is a datetime column to yyyy-Q1, yyyy-Q2, yyyy-Q3, yyyy-Q4
        df['wash_date_quarter'] = df['wash_date'].dt.floor('Q')
    except:
        pass

    return df

def calculate_active_users(df, window_days):
    # Make a copy of the input DataFrame to avoid modifying the original DataFrame
    df_calc = df.copy()

    # Convert the 'date' column to a datetime object
    df_calc['wash_date'] = pd.to_datetime(df_calc['wash_date'])

    # Set the index of the DataFrame to the 'date' column
    df_calc.set_index('wash_date', inplace=True)

    # Group the DataFrame by the user_id column and resample by day, counting the number of unique users per day
    active_users_series = df_calc.groupby('user_id').resample('D')['user_id'].nunique()

    # Create a new DataFrame from the resulting Series and fill any missing values with 0
    active_users_df = active_users_series.to_frame()

    # Rename the columns of the resulting DataFrame
    active_users_df.columns = ['active_users']

    # Shift the 'active_users' column up by one day to calculate the previous day's active users
    active_users_df['prev_day_active_users'] = active_users_df['active_users'].shift(1)

    # Reindex the DataFrame to include all days in the date range
    date_range = pd.date_range(df_calc.index.min(), df_calc.index.max(), freq='D').date
    active_users_df = active_users_df.reindex(date_range)

    # Fill any missing values with 0
    active_users_df.fillna(0, inplace=True)

    # Create a new DataFrame that contains the previous 'window_days' days of unique users for each day in the input DataFrame
    active_users_window = pd.DataFrame()
    for i in range(window_days):
        active_users_window[f'prev_{i+1}_day_active_users'] = active_users_df['prev_day_active_users'].rolling(i+1).sum().shift(-i-1)
    active_users_window.dropna(inplace=True)

    # Reset the index of the resulting DataFrame and rename the column to 'date'
    active_users_window.reset_index(inplace=True)
    active_users_window.rename(columns={'index': 'date'}, inplace=True)

    return active_users_window

def calculate_wash_number(df, window_days):
    # Convert the date column to a datetime object and sort the dataframe by date
    df_calc = df.copy()
    df_calc['date'] = pd.to_datetime(df_calc['wash_date_day'])
    df_calc = df_calc.sort_values('date')

    # Calculate unique user counts for each date and create a time series
    wash_counts = df_calc.groupby(pd.Grouper(key='date', freq='D'))['id'].nunique()
    wash_counts_ts = wash_counts.asfreq('D', fill_value=0)

    # Calculate the rolling window of unique user IDs for each date
    rolling_active_washes = wash_counts_ts.rolling(f'{window_days}D').sum()

    # Reset the index of the resulting dataframe and rename the column
    active_washes_df = pd.DataFrame({'date': rolling_active_washes.index, 'active_washes': rolling_active_washes.values})

    return active_washes_df

def add_logo(logo_path):
    with open(logo_path, "rb") as f:
        image_bytes = f.read()
        encoded_image = base64.b64encode(image_bytes).decode()

    st.markdown(
        f"""
        <style>
            [data-testid="stSidebarNav"] {{
                background-image: url('data:image/png;base64,{encoded_image}');
                background-repeat: no-repeat;
                padding-top: 0px;
                background-position: center top;
                background-size: contain;
                background-size: 250px;
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def calculate_simple_churn(df, lookback_days=100, churning_period=60):
    # Load transaction data into a DataFrame
    transactions = df.copy()

    # Convert the date column to datetime format
    transactions['date'] = pd.to_datetime(transactions['wash_date_day'])

    # Set user_id and date as the index of the DataFrame
    transactions.set_index(['user_id', 'date'], inplace=True)

    # Sort the index by the user_id and date levels
    transactions = transactions.sort_index(level=[0, 1], ascending=[True, True])

    # Create a new DataFrame with a row for each day in the 100 days lookback period
    dates = pd.date_range(start=transactions.index.get_level_values('date').min(), end=transactions.index.get_level_values('date').max())
    daily_users = pd.DataFrame(index=dates)

    # Calculate the churn rate for each day in the lookback period
    for day in daily_users.index:
        # Select transactions within the lookback period
        lookback_start = day - pd.Timedelta(days=lookback_days)
        lookback_end = day
        lookback_transactions = transactions.loc[pd.IndexSlice[:, lookback_start:lookback_end], :]

        # Count the number of unique users who made a purchase within the day
        users = lookback_transactions.index.get_level_values('user_id').unique()
        daily_users.loc[day, 'total_users'] = len(users)

        # Calculate the number of users who churned within the churning period
        churning_end = day + pd.Timedelta(days=churning_period)
        churning_transactions = lookback_transactions.loc[pd.IndexSlice[:, day:churning_end], :]
        churning_users = churning_transactions.index.get_level_values('user_id').unique()
        daily_users.loc[day, 'churned_users'] = len(users) - len(churning_users)

        # Calculate the churn rate for the day
        daily_users.loc[day, 'churn_rate'] = daily_users.loc[day, 'churned_users'] / daily_users.loc[day, 'total_users']
    daily_users.reset_index(inplace=True)
    daily_users.rename(columns={'index': 'date'}, inplace=True)
    return daily_users


def create_user_purchase_df(df):
    # create a copy of the input dataframe
    df_copy = df.copy()
    
    # group transactions by user_id and date_of_purchase
    grouped = df_copy.groupby(['user_id', 'wash_date_day'])

    # create an empty dictionary to store the dataframes for each user
    user_dfs = {}

    # loop through each group of transactions for each user
    for (user_id, wash_date_day), group in grouped:

        # create a new dataframe for this user and date
        user_df = pd.DataFrame(columns=['date', 'user_id', 'transaction_count', 'previous_transaction_date', 'next_transaction_date'])

        # fill in the values for each column using the transactions data for that user
        user_df.loc[0, 'date'] = wash_date_day
        user_df.loc[0, 'user_id'] = user_id
        user_df.loc[0, 'transaction_count'] = len(group)

        # count the number of purchases until that day for this user
        transaction_count = df_copy[(df_copy['user_id'] == user_id) & (df_copy['wash_date_day'] <= wash_date_day)].shape[0]
        user_df.loc[0, 'transaction_count'] = transaction_count

        # get the previous and next transaction dates for this user
        previous_transaction_date = df_copy[(df_copy['user_id'] == user_id) & (df_copy['wash_date_day'] < wash_date_day)]['wash_date_day'].max()
        next_transaction_date = df_copy[(df_copy['user_id'] == user_id) & (df_copy['wash_date_day'] > wash_date_day)]['wash_date_day'].min()

        # fill in the values for prev_purchase_date and next_transaction_date
        if pd.notnull(previous_transaction_date):
            user_df.loc[0, 'previous_transaction_date'] = previous_transaction_date
        if pd.notnull(next_transaction_date):
            user_df.loc[0, 'next_transaction_date'] = next_transaction_date

        # add the new dataframe to the dictionary using the user_id as the key
        if user_id in user_dfs:
            user_dfs[user_id] = pd.concat([user_dfs[user_id], user_df], ignore_index=True)
        else:
            user_dfs[user_id] = user_df

    # concatenate all the dataframes in the dictionary into one big dataframe
    result = pd.concat(user_dfs.values(), ignore_index=True)
    result['days_since_last_purchase'] = (pd.to_datetime(result['date']) - pd.to_datetime(result['previous_transaction_date'])).dt.days
    result['days_until_next_purchase'] = (pd.to_datetime(result['next_transaction_date']) - pd.to_datetime(result['date'])).dt.days
    # convert a date column to datetime format
    result['date'] = pd.to_datetime(result['date'])
    return result


def calculate_user_churn(df, churn_date, churn_period=100, lookback_period=60, wash_count = [1, 1000], show_data=False):
    """
    Calculate user churn for a given date.

    Parameters:
    -----------
    df : pandas DataFrame
        Input DataFrame containing purchase data for all users.
    churn_date : datetime
        Date for which to calculate churn.

    Returns:
    --------
    pandas DataFrame
        DataFrame containing churn rate, previous period user count, churned user count, and total user count.
    """

    # Filter the data for the churn_date
    churn_date_df = df[df['date'] == pd.to_datetime(churn_date)].copy()
    #count washes for this day
    churn_date_df = churn_date_df[(churn_date_df['transaction_count'] >= wash_count[0]) & (churn_date_df['transaction_count'] <= wash_count[1])]
    # Count the number of unique users in the churn_date
    day_user_count = churn_date_df['user_id'].unique()
    day_user_count = len(day_user_count)
    day_wash_count = churn_date_df['user_id'].count()

    # Filter the data for the last 60 days from the churn_date
    prev_period_start = churn_date - pd.DateOffset(days=lookback_period)
    prev_period_end = churn_date - pd.DateOffset(days=0)
    prev_period_df = df[(df['date'] >= pd.to_datetime(prev_period_start)) & (df['date'] <= pd.to_datetime(prev_period_end))].copy()
    
    # get only rows with the latest 'date' for each user
    prev_period_df = prev_period_df.sort_values('date', ascending=False).drop_duplicates('user_id')

    prev_period_df = prev_period_df[(prev_period_df['transaction_count'] >= wash_count[0]) & 
                                    (prev_period_df['transaction_count'] <= wash_count[1])]
    
    # Count the number of unique users in the previous period
    prev_period_users = prev_period_df['user_id'].unique()
    prev_period_user_count = len(prev_period_users)

    # Filter the data for the next 100 days from the churn_date
    next_period_start = churn_date + pd.DateOffset(days=1)
    next_period_end = churn_date + pd.DateOffset(days=churn_period)
    # next_period_df = df[(df['date'] >= pd.to_datetime(next_period_start)) & (df['date'] <= pd.to_datetime(next_period_end))].copy()

    next_period_df = prev_period_df[prev_period_df['days_until_next_purchase'] <= churn_period].copy()

    # Count the number of unique users in the next period
    next_period_users = next_period_df['user_id'].unique()
    next_period_user_count = len(next_period_users)

    # Count the number of users who churned in the next period
    churned_user_count = len(prev_period_users) - len(next_period_users)

    # Calculate the churn rate
    churn_rate = churned_user_count / prev_period_user_count if prev_period_user_count != 0 else np.nan

    # Create a DataFrame with the results
    result_df = pd.DataFrame({
        'date': [churn_date],
        'day_user_count': [day_user_count],
        'day_wash_count': [day_wash_count],

        'prev_period_start': [prev_period_start],
        'prev_period_end': [prev_period_end],
        'prev_period_user_count': [prev_period_user_count],

        'next_period_start': [next_period_start],
        'next_period_end': [next_period_end],

        'churned_user_count': [churned_user_count],
        'churn_rate': [churn_rate]
    })

    return result_df


def calculate_churn_for_date_range(df, start_date, end_date, churn_period=100, lookback_period=60, wash_count = [1, 1000], show_data=False):
    """
    Calculate the churn rate for each day in the given date range.

    Parameters:
    -----------
    df : pandas.DataFrame
        Input dataframe containing user purchase information.
    start_date : str or datetime.datetime
        The start date of the date range to calculate churn for.
    end_date : str or datetime.datetime
        The end date of the date range to calculate churn for.
    churn_period : int, optional (default=100)
        The number of days after the churn date to consider for churn rate calculation.
    lookback_period : int, optional (default=60)
        The number of days before the churn date to consider for churn rate calculation.

    Returns:
    --------
    result_df : pandas.DataFrame
        A dataframe containing the churn rate for each day in the given date range.
    """
    # convert start_date and end_date to datetime objects if they are strings
    if isinstance(start_date, str):
        start_date = pd.to_datetime(start_date)
    if isinstance(end_date, str):
        end_date = pd.to_datetime(end_date)

    result = []
    for date in pd.date_range(start=start_date, end=end_date, freq='D'):
        # print(date)
        result.append(calculate_user_churn(df, date, churn_period=churn_period, lookback_period=lookback_period, wash_count=wash_count))

    result_df = pd.concat(result, ignore_index=True)
    
    if show_data:
        st.write(result_df)
        st.download_button(label="Download churn data",
                           data=result_df.to_csv(index=False),
                           file_name='churn_data.csv',
                           mime='text/csv')
    # convert wash count to string
    wash_count_s = str(wash_count[0]) + '-' + str(wash_count[1])
    result_df['wash_count'] = wash_count_s
    return result_df