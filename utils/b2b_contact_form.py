import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from utils.custom_functions import *
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
from PIL import Image
from datetime import datetime

def add_picture_to_streamlit(image_path, caption = None):
    image = Image.open(image_path)
    st.image(image, caption=caption)

    hide_img_fs = '''
        <style> 
            button[title="View fullscreen"]{
                visibility: hidden;}
        </style>
    '''

    st.markdown(hide_img_fs, unsafe_allow_html=True)

def send_email(recipient_address, subject, body):
    # create a message object
    msg = MIMEMultipart()
    msg['From'] = st.secrets['email']['smtp_username']
    msg['To'] = recipient_address
    msg['Subject'] = subject

    # add some text to the email body allow use html
    msg.attach(MIMEText(body, 'html'))
    #msg.attach(MIMEText(body, 'plain'))

    # create a SMTP client session
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    smtp_username = st.secrets['email']['smtp_username']
    smtp_password = st.secrets['email']['smtp_password']
    with smtplib.SMTP(smtp_server, smtp_port) as smtp:
        smtp.starttls()
        smtp.login(smtp_username, smtp_password)
        smtp.send_message(msg)

def create_b2b_form(authenticator, username, name, config):

    email_list_to_us = ["ittone@gmail.com"] #ez az email cimre fogja elkuldeni a rendeles adatait

    # nyitvatartas
    #nyitvatartas_df = pd.read_csv('data/cleango_b2b_nyitvatartas - adatok.csv')
    sheet_id = '1T0aljTRIyMcimuvTY1aWY_aPX4kwnV2gtl1EMIXB8g0'

    # Construct the URL for the sheet's CSV export
    csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    nyitvatartas_df = pd.read_csv(csv_url)
    # filter for dates that is higher than today
    nyitvatartas_df = nyitvatartas_df[nyitvatartas_df['date'] >= datetime.now().strftime('%Y-%m-%d')]
    nyitvatartas_df_nyitva_list = nyitvatartas_df[nyitvatartas_df['nyitva'] == 'igen']['date_time'].tolist()

    sheet_id_extrak = '1cFnHml4mtuMQTtk4bplRUKkV3XWDj4_E4x2ED-8wRH0'
    csv_extrak_url = f"https://docs.google.com/spreadsheets/d/{sheet_id_extrak}/export?format=csv&gid=0"
    extrak_df = pd.read_csv(csv_extrak_url)
    extrak_df_list = extrak_df['extra_nev'].tolist()

    # load auto markak
    auto_markak_df = pd.read_csv('data/auto_markak_tipusok.csv')
    auto_markak_tipusok_list = auto_markak_df['brand_make_name']
    # add a blank option to the beginning of the list
    auto_markak_tipusok_list = [''] + auto_markak_tipusok_list.tolist()

    col1, col2, col3 = st.columns([6, 1, 1])
    with col1:
        st.write("Wellcome {}. You are logged in as {}.".format(name, username))
    with col3:
        authenticator.logout('Logout', 'main')

    st.markdown("### Autómosást az alábbi ürlap kitöltésével addhatsz le. Add meg a rendelés adatait, majd kattints a lap alján található Rendelés gombra")
    st.markdown("***")
    
    st.markdown('### Mosás időpontja, Mosás helyszíne')
    col1, col2 = st.columns([2, 2])
    with col1:
        mosas_datum_ido = st.selectbox("Mosás dátuma és időpontja", nyitvatartas_df_nyitva_list)
    helyszin = st.text_input("Mosás helye (pl. 1111 Budapest, Kossuth Lajos utca 1.)")

    
    st.markdown('### Mosandó autó adatai')
    col1, col2 = st.columns([2, 2])
    with col1:
        number_plate = st.text_input("Rendszám")
        auto_markak_tipusok = st.selectbox("Auto márka tipus", auto_markak_tipusok_list)
    
    st.markdown('### Milyen mosást szerentél rendelni?')
    col1, col2 = st.columns([2, 2])
    with col1:
        alapszolg = st.radio("Alapszolgáltatás", ("Külső + Belső", "Csak Külső", "Csak Belső"))
    with col2:
        extrak = st.multiselect("Extrák", extrak_df_list)

    st.markdown('### Kapcsolat')
    col1, col2 = st.columns([2, 2])
    with col1:
        nev = st.text_input("Név")
    col1, col2 = st.columns([2, 2])
    with col1:
        email_user = st.text_input("E-mail")
    with col2:
        telefon = st.text_input("Telefon")
    # create default szamlazasi infok that is changed based on the username
    try:
        szamlazasi_infok_default = config['credentials']['usernames'][username]['szamlazasi_cim']
    except:
        szamlazasi_infok_default = "Add meg a szamlási címet"
    st.markdown('### Számlázasi Információk')
    szamlazasi_info_radio = st.radio("Számlázási információk", (szamlazasi_infok_default, "Egyéb"))
    if ((szamlazasi_info_radio == "Egyéb") or (szamlazasi_info_radio == "Add meg a számlázasi cimet")):
        szamlazasi_infok = st.text_input("Számlázasi Informáciok (Név, Adószám, Iranyítomszám, Város, Utca, Házszám)")
    else:
        szamlazasi_infok = szamlazasi_info_radio

    st.markdown('### Megjegyzés')
    megjegyzes = st.text_area("Megjegyzés")
    email_subject = "B2B mosás rendelés érkezett - {}".format(username)

    email_body_to_us = 'Űj mosás rendelés érkezett a B2B rendszerén keresztül!</p> <br><br> Ügyfel név: <br> {} <br><br> Mosando autó: <br> Rendszám: {} <br> Autó Márka és típus: {} <br><br> Mosás helyszin: <br> {} <br> Mosás időpontja: {} <br><br> Milyen mosást szerente rendelni? <br> {}, <br> Extrák: <br> {} <br><br>Kapcsolat: <br> {} <br> {}, {} <br><br> Számlázási információk: <br> {} <br><br> Megjegyzés: <br> {} <br>'.format(
        username, number_plate, auto_markak_tipusok, helyszin, mosas_datum_ido, alapszolg, extrak, nev, email_user, telefon, szamlazasi_infok, megjegyzes)
    email_body_to_user = 'Köszönjük megrendelését a CleanGo B2B rendszerén keresztül! Rendelését megkaptuk.</p> <br><br> Mergrendelő felhasználó neve: <br> {} <br><br> Mosando autó: <br> Rendszám: {} <br> Autó Márka és típus: {} <br><br> Mosás helyszin: <br> {} <br> Mosás időpontja: {} <br><br> Milyen mosást szerente rendelni? <br> {}, <br> Extrák: <br> {} <br><br>Kapcsolat: <br> {} <br> {}, {} <br><br> Számlázási információk: <br> {} <br><br> Megjegyzés: <br> {} <br>'.format(
        username, number_plate, auto_markak_tipusok, helyszin, mosas_datum_ido, alapszolg, extrak, nev, email_user, telefon, szamlazasi_infok, megjegyzes)


    col1, col2 = st.columns([2, 2])

    with col1:

        if st.button("Send Order"):
            
            # send the email to CleanGo
            for email_adress_to_us in email_list_to_us:
                try:
                    send_email(email_adress_to_us, email_subject, email_body_to_us)
                    st.write("Köszönjük a megrendelését, megkaptuk a megrendelését. A megrendelését a lehető leghamarabb feldolgozzuk. A megrendelésis visszaigazolást az alábbi megadott email címre is elküldtük.")
                    # st.write("Megrendelését elküldtük a következő emailcimre: {}!".format(email_adress_to_us))
                except:
                    st.write("Hoppá valami hiba történt. A megrendelését nem tudtuk elküldeni!")
            
            # send the email to the user
            try:
                send_email(email_user, "CleanGo B2B Rendeles Visszaigazolas", email_body_to_user)
                st.write(" {}".format(email_user))
            except:
                st.write("Hoppá valami hiba történt. A megrendelését nem tudtuk elküldeni!")
    
    with col2:
        st.write("If something went wrong you can reach us via:")
        st.write("Email: info@cleango.hu")
        st.write("Phone: +36 30 141 5100")