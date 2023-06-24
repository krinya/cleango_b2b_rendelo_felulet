import pymysql
import paramiko
import pandas as pd
import streamlit as st
import io

def sql_query(query_string, type = 'simple'):

    if type == 'simple':
        hostname = st.secrets['simple']['hostname'] #MySQL Host
        username = st.secrets['simple']['sql_username'] #username
        pw = st.secrets['simple']['pw'] #password
        port = st.secrets['simple']['port'] #port
        main_db = st.secrets['simple']['sql_main_database'] #database
        
        # Establish a connection to the database
        conn = pymysql.connect(host=hostname, port=port, user=username, passwd=pw, db=main_db)
    
        # Execute the SQL query and retrieve data
        query = query_string
        data = pd.read_sql_query(query, conn)
    
        # Close the database connection
        conn.close()

    return data

def create_connection(type='simple'):

    if type == 'simple':
        hostname = st.secrets['simple']['hostname'] #MySQL Host
        username = st.secrets['simple']['sql_username'] #username
        pw = st.secrets['simple']['pw'] #password
        port = st.secrets['simple']['port'] #port
        main_db = st.secrets['simple']['sql_main_database'] #database
        
        # Establish a connection to the database
        conn = pymysql.connect(host=hostname, port=port, user=username, passwd=pw, db=main_db)

    return conn
