import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from utils.custom_functions import *
from utils.b2b_contact_form import *
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

st.set_page_config(layout='wide')

col1, col2 = st.columns([2, 8])
with col1:
    add_picture_to_streamlit('data/cleango-logo-small.png', caption = None)

# create a Streamlit app

st.title("B2B Rendelő felület")

# password_to_hash = st.text_input("Password to hash")
# hashed_passwords = stauth.Hasher([password_to_hash]).generate()
# st.write("Hashed passwords")
# st.write(hashed_passwords)

with open('.streamlit/b2b_users_data.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

col1, col2 = st.columns([6, 3])

with col1:
    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days'],
        config['preauthorized'])
    name, authentication_status, username = authenticator.login('Login', 'main')
with col2:
    if authentication_status == False or authentication_status == None:
        add_picture_to_streamlit('data/mosas.png', caption = None)
    
if authentication_status:
    if username == 'admin':
        st.markdown('You are logged in as admin.')
        st.markdown("You can use the following link to edid the opening hours: [Opening Hours](https://docs.google.com/spreadsheets/d/1T0aljTRIyMcimuvTY1aWY_aPX4kwnV2gtl1EMIXB8g0/edit#gid=0)")
        authenticator.logout('Logout', 'main')
    else:
        create_b2b_form(authenticator=authenticator, username=username, name=name, config=config)
elif authentication_status == False:
    with col1:
        st.error('Username/password is incorrect')
elif authentication_status == None:
    with col1:
        st.warning('Please enter your username and password')
        st.write("If you don't have an account, please contact us at: info@cleango.hu")