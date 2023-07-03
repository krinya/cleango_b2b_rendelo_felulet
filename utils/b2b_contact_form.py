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
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

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
    smtp_server = 'smtp.eu.mailgun.org'
    smtp_port = 587
    smtp_username = st.secrets['email']['smtp_username']
    smtp_password = st.secrets['email']['smtp_password']
    with smtplib.SMTP(smtp_server, smtp_port) as smtp:
        smtp.starttls()
        smtp.login(smtp_username, smtp_password)
        smtp.send_message(msg)

def session_counter():
    # st.sesson counter intialization
    if 'session_counter' not in st.session_state:
        st.session_state.session_counter = 1
    st.session_state.session_counter = 1
    return st.session_state.session_counter

def create_b2b_form(authenticator, username, name, config):

    email_list_to_us = ["info@cleango.hu"] #ez az email cimre fogja elkuldeni a rendeles adatait

    # nyitvatartas
    #nyitvatartas_df = pd.read_csv('data/cleango_b2b_nyitvatartas - adatok.csv')
    sheet_id = '1T0aljTRIyMcimuvTY1aWY_aPX4kwnV2gtl1EMIXB8g0'

    # Construct the URL for the sheet's CSV export
    csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    nyitvatartas_df = pd.read_csv(csv_url)
    # crete a date_time column from date and time columns
    nyitvatartas_df['date_time_2'] = nyitvatartas_df['date'].astype(str) + ' ' + nyitvatartas_df['time'].astype(str)
    st.dataframe(nyitvatartas_df)
    # convert date_time column to datetime
    nyitvatartas_df['date_time_3'] = pd.to_datetime(nyitvatartas_df['date_time_2'], format='%Y-%m-%d %H')
    st.dataframe(nyitvatartas_df)
    nyitvatartas_df = nyitvatartas_df[nyitvatartas_df['date_time_3'] >= datetime.now()]
    st.dataframe(nyitvatartas_df)
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
        st.write("Kapcsolat: +36 30 141 5100 \n\n{}, üdvözli a CleanGo. Az alábbi userrel van bejelentkezve: {}.".format(name, username))
    with col3:
        authenticator.logout('Logout', 'main')

    with st.form(key='b2b_form'):

        col1, col2, col3 = st.columns([6, 1, 1])

        st.markdown("### Autómosást az alábbi űrlap kitöltésével tud leadni.")
        st.write("Adja meg a rendelés adatait, majd kattintson a lap alján található 'Megrendelés Elküldése' gombra.")
        
        st.markdown('### 1. Mosás időpontja és helyszíne')
        st.markdown("Kérjük adja meg a mosás időpontját, valamint a mosás helyszínét. \n\n Mosást csak akkor tudunk fogadni, ha a megadott időpontban nyitva vagyunk, vagy van még szabad kapacitásunk.")
    
        col1, col2 = st.columns([2, 2])
        with col1:
            mosas_datum_ido = st.selectbox("Mosás dátuma és időpontja* (kötelező)", nyitvatartas_df_nyitva_list)

            try:
                helyszin_default = config['credentials']['usernames'][username]['wash_address']
                # convert helyszin_default to a list if it is not a list
                if type(helyszin_default) != list:
                    helyszin_default = [helyszin_default]
                # add 'Egyeb' to the end of the list
                helyszin_default.append("Egyéb")
            except:
                helyszin_default = "Adja meg a mosás helyét!"

        with col1:
            try:
                helyszin_radio = st.radio("Mosás helye* (kötelező)", helyszin_default)
                helyszin_text = st.text_input("Egyedi cim vagy az egyéb valasztas eseten a Mosás helye (pl. 1111 Budapest, Kossuth Lajos utca 1.)")
                #if (helyszin_radio == 'Egyéb') | (helyszin_default == "Adja meg a mosás helyét!"):
                #    helyszin = st.text_input("Mosás helye (pl. 1111 Budapest, Kossuth Lajos utca 1.)")
                #else:
                helyszin = helyszin_radio
            except:
                helyszin = st.text_input("Mosás helye (pl. 1111 Budapest, Kossuth Lajos utca 1.)")

        
        st.markdown('### 2. Mosandó autó adatai')
        col1, col2 = st.columns([2, 2])
        with col1:
            number_plate = st.text_input("Rendszám* (kötelező)")
            auto_markak_tipusok = st.selectbox("Auto márka és típus* (kötelező)", auto_markak_tipusok_list)
        
        st.markdown('### 3. Milyen típusú mosást szeretne rendelni?')
        col1, col2 = st.columns([2, 2])
        with col1:
            alapszolg = st.radio("Alapszolgáltatás* (kötelező)", ("Külső + Belső", "Csak külső", "Csak belső"))
        with col2:
            extrak = st.multiselect("Extrák* (kötelező)", extrak_df_list)

        st.markdown('### 4. Kapcsolat')
        st.markdown("Kérjük adjon meg olyan adatokat, amin ha szükséges el tudjuk érni.")
        col1, col2 = st.columns([2, 2])
        with col1:
            nev = st.text_input("Név (opcionális)")
        col1, col2 = st.columns([2, 2])
        with col1:
            email_user = st.text_input("E-mail* (kötelező)")
        with col2:
            telefon = st.text_input("Telefon (opcionális)")
            # create default szamlazasi infok that is changed based on the username
        with col1:
            try:
                szamlazasi_infok_default = config['credentials']['usernames'][username]['szamlazasi_cim']
                # convert szamlazasi_infok_default to a list if it is not a list
                if type(szamlazasi_infok_default) != list:
                    szamlazasi_infok_default = [szamlazasi_infok_default]
                    # add 'Egyeb' to the end of the list
                szamlazasi_infok_default.append("Egyéb")
            except:
                szamlazasi_infok_default = ["Adja meg a számlázási címet"]
            st.markdown('### 5. Számlázási információk')
            szamlazasi_info_radio = st.radio("Számlázási információk* (kötelező)", szamlazasi_infok_default)
            szamlazasi_info_text = st.text_input("Egyedi számlazasi cím vagy az egyéb valasztás esetén a Számlázási Informáciok (Név, Adószám, Irányítomszám, Város, Utca, Házszám)")
        #if ((szamlazasi_info_radio == "Egyéb") or (szamlazasi_info_radio == "Add meg a számlázási cimet")):
        #    szamlazasi_infok = st.text_input("Számlázási Informáciok (Név, Adószám, Irányítomszám, Város, Utca, Házszám)")
        #else:
        szamlazasi_infok = szamlazasi_info_radio

        st.markdown('### 6. Megjegyzés')
        st.markdown("Ha van még valami, amit szeretne közölni velünk, akkor írja be az alábbi mezőbe.")
        megjegyzes = st.text_area("Megjegyzés (opcionális)")
        email_subject = "B2B mosás rendelés érkezett - {}".format(username)

        submitted = st.form_submit_button("Megrendelés elküldése", on_click=session_counter)

        col1, col2 = st.columns([2, 2])

        with col1:

            st.markdown("Nyomja meg a gombot, hogy a megrendelését elküldje nekünk.")
            #st.markdown("Ha megnyomja a gombot, és nem lát semmilyen egyéb üzenetet, ez alatt a mondat alatt, akkor nyomja meg a gombot újra.")
        with col2:
            st.write("Ha valami kérdése van, kérjük keressen minket bizalommal a következő elérhetőségeken:")
            st.write("Email: info@cleango.hu")
            st.write("Telefon: +36 30 141 5100")

        if submitted:
            print("submitted")
        if st.session_state.session_counter == 1:
            with st.spinner("Megrendelés elküldése folyamatban..."):
                st.session_state.session_counter = 0
                with col1:
                    # some checks
                    error_counter = 0

                    if (szamlazasi_info_radio == "Egyéb") or (szamlazasi_info_radio == "Add meg a számlázási cimet"):
                        szamlazasi_infok = szamlazasi_info_text
                        if len(szamlazasi_infok) < 3:
                            st.warning("Kérjük adja meg a számlázási információkat!")
                            error_counter += 1

                    if len(number_plate) < 1:
                        st.warning("Kérjük adja meg a rendszámot!")
                        error_counter += 1
                    
                    if len(auto_markak_tipusok) < 1:
                        st.warning("Kérjük adja meg az autó márkáját és típusát!")
                        error_counter += 1

                    if (helyszin_radio == 'Egyéb') | (helyszin_default == "Adja meg a mosás helyét!"):
                        helyszin = helyszin_text
                        if len(helyszin) < 3:
                            st.warning("Kérjük adja meg a mosás helyét!")
                            error_counter += 1
                    
                    # chech email_user must contain @ and .
                    if email_user.find("@") == -1:
                        st.warning("Kérjük adjon meg egy valós e-mail címet!")
                        error_counter += 1

                    # chech email_user must contain @ and .
                    if email_user.find(".") == -1:
                        st.warning("Kérjük adjon meg egy valós e-mail címet!")
                        error_counter += 1

                    # ehcek if extrak is greater than 1
                    if len(extrak) > 1:
                        # if extrak contains 'nem kérek extrát' then show warning
                        if 'nem kérek extrát' in extrak:
                            st.warning("Ha nem kért extrát, akkor ne válasszon ki más extrát.")
                            error_counter += 1
                    
                    if len(extrak) < 1:
                        st.warning("Kérjük válasszon ki legalább egy extrát, vagy valassza ki hogy nem kér extrát!")
                        error_counter += 1

                    if error_counter == 0:
 
                        megjegyzes = megjegyzes.replace('\n', '')

                        answer_dict = {
                            "username": username,
                            "email_user": email_user,
                            "number_plate": number_plate,
                            "auto_markak_tipusok": auto_markak_tipusok,
                            "helyszin": helyszin,
                            "mosas_datum_ido": mosas_datum_ido,
                            "alapszolg": alapszolg,
                            "extrak": extrak,
                            "nev": nev,
                            "szamlazasi_infok": szamlazasi_infok,
                            "megjegyzes": megjegyzes
                        }

                        answer_dict_str = str(answer_dict)

                        email_body_to_us = 'Új mosás rendelés érkezett a B2B rendszerén keresztül!</p> <br><br> Ügyfél név: <br> {} <br><br> Mosandó autó: <br> Rendszám: {} <br> Autómárka és típus: {} <br><br> Mosás helyszín: <br> {} <br> Mosás időpontja: {} <br><br> Milyen mosást szerente rendelni? <br> {}, <br> Extrák: <br> {} <br><br>Kapcsolat: <br> {} <br> {}, {} <br><br> Számlázási információk: <br> {} <br><br> Megjegyzés: <br> {} <br>'.format(
                            username, number_plate, auto_markak_tipusok, helyszin, mosas_datum_ido, alapszolg, extrak, nev, email_user, telefon, szamlazasi_infok, megjegyzes)
                        email_body_to_user = 'Köszönjük megrendelését a CleanGo - B2B rendszerén keresztül! Rendelését megkaptuk.</p> <br><br>Ez egy automatikusan generált email, kérjük ne válaszoljon rá!<br><br> Mergrendelő felhasználó neve: <br> {} <br><br> Mosandó autó: <br> Rendszám: {} <br> Autómárka és típus: {} <br><br> Mosás helyszín: <br> {} <br> Mosás időpontja: {} <br><br> Milyen mosást szerente rendelni? <br> {}, <br> Extrák: <br> {} <br><br>Kapcsolat: <br> {} <br> {}, {} <br><br> Számlázási információk: <br> {} <br><br> Megjegyzés: <br> {} <br><br><br> Ha a autómosását le szeretné mondani vagy másik időpontra foglalná át kérem vegye fel a kapcsolatot velünk emailben: info@cleango.hu vagy telefonon: +36301415100 <br><br>'.format(
                            username, number_plate, auto_markak_tipusok, helyszin, mosas_datum_ido, alapszolg, extrak, nev, email_user, telefon, szamlazasi_infok, megjegyzes)

                        conn = create_connection()
                        cursor = conn.cursor()
                        # I have these columns in the table: id, name, email, telephone_number, dob, questions, created_at, updated_at.
                        # The id and the created_at and updated_at columns are automatically filled by the database.
                        insert_query = """INSERT INTO cleango.bi_b2b_orders_registration (username, nev, email_user, mosas_datum_ido, answer_text) VALUES  ('{}', '{}', '{}', '{}', '{}')""".format(
                            username,
                            nev,
                            email_user,
                            mosas_datum_ido,
                            answer_dict_str.replace("'", "''")
                        )
                        cursor.execute(insert_query)
                        # Commit the changes and close the cursor and the database connection
                        conn.commit()
                        cursor.close()
                        conn.close()
                            
                        # send the email to CleanGo
                        for email_adress_to_us in email_list_to_us:
                            try:
                                send_email(email_adress_to_us, email_subject, email_body_to_us)
                                st.write("Megrendelését a CleanGo megkapta. A megrendelését a lehető leghamarabb feldolgozzuk.")
                            except:
                                st.write("Hoppá valami hiba történt. A megrendelését a CleanGo nem kapta meg.")
                            
                        # send the email to the user
                        try:
                            send_email(email_user, "CleanGo - B2B Rendelés Visszaigazolás", email_body_to_user)
                            st.write("A megrendelési visszaigazolást az alábbi megadott email címre is elküldtük.")
                            st.write(" {}".format(email_user))
                            st.write("Kérjük ellenőrizze a spam mappát is!")
                        except:
                            st.write("Hoppá valami hiba történt. A visszaigazolást nem tudtuk tudtuk elküldeni az alább megadott emailcimre!")
                            st.write("{}".format(email_user))
