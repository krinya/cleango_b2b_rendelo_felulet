import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from utils.custom_functions import *
from utils.b2b_contact_form import *
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

#set streamlit page name
st.set_page_config(page_title='CleanGo - B2B Rendelő felület', page_icon='data/cleango-logo-small.png', layout='wide')

col1, col2 = st.columns([2, 8])
with col1:
    add_picture_to_streamlit('data/cleango-logo-small.png', caption = None)

# create a Streamlit app

st.title("B2B Rendelő felület", anchor=None)

if 'name' not in st.session_state:
    st.session_state.name = None
if 'authentication_status' not in st.session_state:
    st.session_state.authentication_status = None
if 'username' not in st.session_state:
    st.session_state.username = None

with open('.streamlit/b2b_users_data.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)
    st.session_state.config = config

col1, col2 = st.columns([6, 3])

with col1:
    st.session_state.authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days'],
        config['preauthorized'])
    st.session_state.name, st.session_state.authentication_status, st.session_state.username = st.session_state.authenticator.login('Login', 'main')

with col2:
    if st.session_state.authentication_status == False or st.session_state.authentication_status == None:
        add_picture_to_streamlit('data/mosas.png', caption = None)
    
if st.session_state.authentication_status:

    email_list_to_us = ["info@cleango.hu"] #ez az email cimre fogja elkuldeni a rendeles adatait

    # nyitvatartas
    #nyitvatartas_df = pd.read_csv('data/cleango_b2b_nyitvatartas - adatok.csv')
    sheet_id = '1T0aljTRIyMcimuvTY1aWY_aPX4kwnV2gtl1EMIXB8g0'

    # Construct the URL for the sheet's CSV export
    csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    if 'nyitvatartas_df' not in st.session_state:
        st.session_state.nyitvatartas_df = pd.read_csv(csv_url)
        # crete a date_time column from date and time columns
        st.session_state.nyitvatartas_df['date_time_2'] = st.session_state.nyitvatartas_df['date'].astype(str) + ' ' + st.session_state.nyitvatartas_df['time'].astype(str)
        st.session_state.nyitvatartas_df['date_time_2'] = st.session_state.nyitvatartas_df['date_time_2'].str.replace(r'\b(\d)\b', r'0\1', regex=True)
        st.session_state.nyitvatartas_df['date_time_2'] = st.session_state.nyitvatartas_df['date_time_2'].astype(str) + f""":00"""
        # convert date_time column to datetime
        st.session_state.nyitvatartas_df['date_time_3'] = pd.to_datetime(st.session_state.nyitvatartas_df['date_time_2'], infer_datetime_format=True, errors='coerce')
        st.session_state.nyitvatartas_df = st.session_state.nyitvatartas_df[st.session_state.nyitvatartas_df['date_time_3'] >= datetime.now() + pd.Timedelta(hours=2)]
    
    nyitvatartas_df_nyitva_list = st.session_state.nyitvatartas_df[st.session_state.nyitvatartas_df['nyitva'] == 'igen']['date_time'].tolist()
    
    if 'extrak_df' not in st.session_state:
        sheet_id_extrak = '1cFnHml4mtuMQTtk4bplRUKkV3XWDj4_E4x2ED-8wRH0'
        csv_extrak_url = f"https://docs.google.com/spreadsheets/d/{sheet_id_extrak}/export?format=csv&gid=0"
        st.session_state.extrak_df = pd.read_csv(csv_extrak_url)

    if st.session_state.username =='hellenergy':
        extrak_df_list = st.session_state.extrak_df['extra_nev_hellenergy'].tolist()
    else:
        extrak_df_list = st.session_state.extrak_df['extra_nev'].tolist()
    # delete nan values from the list
    extrak_df_list = [x for x in extrak_df_list if str(x) != 'nan']

    # load auto markak
    if 'auto_markak_df' not in st.session_state:
        st.session_state.auto_markak_df = pd.read_csv('data/auto_markak_tipusok.csv')
    if 'auto_markak_tipusok_list' not in st.session_state:
        st.session_state.auto_markak_tipusok_list = st.session_state.auto_markak_df['brand_make_name']
        # add a blank option to the beginning of the list
        st.session_state.auto_markak_tipusok_list = [''] + st.session_state.auto_markak_tipusok_list.tolist()

    
    col1, col2, col3 = st.columns([6, 1, 1])
    with col1:
        st.write("Kapcsolat: +36 30 141 5100 \n\n{}, üdvözli a CleanGo. Az alábbi userrel van bejelentkezve: {}.".format(st.session_state.name, st.session_state.username))
    with col3:
        st.session_state.authenticator.logout('Logout', 'main')

    main_container = st.container(border=True)

    with main_container:
        col1, col2, col3 = st.columns([6, 1, 1])

        st.markdown("### Autómosást az alábbi űrlap kitöltésével tud leadni.")
        st.write("Adja meg a rendelés adatait, majd kattintson a lap alján található 'Megrendelés Elküldése' gombra.")
            
        st.markdown('### 1. Mosás időpontja és helyszíne')
        st.markdown("Kérjük adja meg a mosás időpontját, valamint a mosás helyszínét. \n\n Mosást csak akkor tudunk fogadni, ha a megadott időpontban nyitva vagyunk, vagy van még szabad kapacitásunk.")
        
        col1, col2 = st.columns([2, 2])
        with col1:
            st.selectbox("Mosás dátuma és időpontja* (kötelező)", nyitvatartas_df_nyitva_list, key='mosas_datum_ido')

            try:
                helyszin_default = st.session_state.config['credentials']['usernames'][st.session_state.username]['wash_address']
                # convert helyszin_default to a list if it is not a list
                if type(helyszin_default) != list:
                    helyszin_default = [helyszin_default]
                # add 'Egyeb' to the end of the list
                helyszin_default.append("Egyéb")
            except:
                helyszin_default = "Adja meg a mosás helyét!"

        with col1:
            try:
                st.radio("Mosás helye* (kötelező)", helyszin_default, key='helyszin_radio')
                st.text_input("Egyedi cim vagy az egyéb valasztas eseten a Mosás helye (pl. 1111 Budapest, Kossuth Lajos utca 1.)",
                                key='helyszin_text')
            except:
                st.text_input("Mosás helye (pl. 1111 Budapest, Kossuth Lajos utca 1.)", key='helyszin_text')

            try:
                if st.session_state.helyszin_radio == "Egyéb":
                    st.session_state.helyszin = st.session_state.helyszin_text
                else:
                    st.session_state.helyszin = st.session_state.helyszin_radio
            except:
                st.session_state.helyszin = st.session_state.helyszin_text

        
        st.markdown('### 2. Mosandó autó adatai')
        col1, col2 = st.columns([2, 2])
        with col1:
            st.text_input("Rendszám* (kötelező)", key='number_plate')
            st.selectbox("Auto márka és típus* (kötelező)", st.session_state.auto_markak_tipusok_list, key='auto_markak_tipusok')
        
        st.markdown('### 3. Milyen típusú mosást szeretne rendelni?')
        col1, col2 = st.columns([2, 2])
        with col1:
            st.radio("Alapszolgáltatás* (kötelező)", ("Külső + Belső", "Csak külső", "Csak belső"), key='alapszolg')
        with col2:
            st.multiselect("Extrák listája:* (kötelező)", extrak_df_list, key='extrak')

        st.markdown('### 4. Kapcsolat')
        st.markdown("Kérjük adjon meg olyan adatokat, amin ha szükséges el tudjuk érni.")
        col1, col2 = st.columns([2, 2])
        with col1:
            st.text_input("Név (opcionális)", key='nev')
        col1, col2 = st.columns([2, 2])
        with col1:
            st.text_input("E-mail* (kötelező)", key='email_user')
        with col2:
            st.text_input("Telefon (opcionális)", key='telefon')
            # create default szamlazasi infok that is changed based on the username
        with col1:
            try:
                szamlazasi_infok_default = st.session_state.config['credentials']['usernames'][st.session_state.username]['szamlazasi_cim']
                # convert szamlazasi_infok_default to a list if it is not a list
                if type(szamlazasi_infok_default) != list:
                    szamlazasi_infok_default = [szamlazasi_infok_default]
                    # add 'Egyeb' to the end of the list
                szamlazasi_infok_default.append("Egyéb")
            except:
                szamlazasi_infok_default = ["Adja meg a számlázási címet"]
            st.markdown('### 5. Számlázási információk')
            st.radio("Számlázási információk* (kötelező)", szamlazasi_infok_default, key='szamlazasi_info_radio')
            st.text_input("Egyedi számlazasi cím vagy az egyéb valasztás esetén a Számlázási Informáciok (Név, Adószám, Irányítomszám, Város, Utca, Házszám)",
                          key='szamlazasi_info_text')
            try:
                if st.session_state.szamlazasi_info_radio == "Egyéb":
                    st.session_state.szamlazasi_infok = st.session_state.szamlazasi_info_text
                else:
                    st.session_state.szamlazasi_infok = st.session_state.szamlazasi_info_radio
            except:
                st.session_state.szamlazasi_infok = st.session_state.szamlazasi_info_text


        st.markdown('### 6. Megjegyzés')
        st.markdown("Ha van még valami, amit szeretne közölni velünk, akkor írja be az alábbi mezőbe.")
        st.text_area("Megjegyzés (opcionális)", key='megjegyzes_text_area')

    
    
    st.markdown('### A rendelés összegzése')
    st.markdown("Kérjük ellenőrizze, hogy minden adatot helyesen adott-e meg. Ha valamit módosítani szeretne, akkor még feljebb az adott mezőt módosíthatja. Ha minden adat helyes, akkor kattintson a 'Megrendelés elküldése' gombra.")
    osszegzes_container = st.container(border=True)
    with osszegzes_container:
        st.markdown("**Mosás dátuma és időpontja:** {}".format(st.session_state.mosas_datum_ido))
        st.markdown("**Mosás helye:** {}".format(st.session_state.helyszin))
        st.markdown("**Rendszám:** {}".format(st.session_state.number_plate))
        st.markdown("**Autó márkája és típusa:** {}".format(st.session_state.auto_markak_tipusok))
        st.markdown("**Alapszolgáltatás:** {} autómosás".format(st.session_state.alapszolg))
        st.markdown("**Extrák listája:** {}".format(st.session_state.extrak))
        st.markdown("**Név:** {}".format(st.session_state.nev))
        st.markdown("**E-mail:** {}".format(st.session_state.email_user))
        st.markdown("**Telefon:** {}".format(st.session_state.telefon))
        st.markdown("**Számlázási információk:** {}".format(st.session_state.szamlazasi_infok))
        st.markdown("**Megjegyzés:** {}".format(st.session_state.megjegyzes_text_area))


    email_subject = "B2B mosás rendelés érkezett - {}".format(st.session_state.username)

    if 'button_press_counter' not in st.session_state:
        st.session_state['button_press_counter'] = 0
    
    def megrendeles_button_press():
        st.session_state['button_press_counter'] = 1

    submitted = st.button("Megrendelés elküldése", key='subbmit_button_final', on_click=megrendeles_button_press)

    col1, col2 = st.columns([3, 2])

    with col1:

        st.markdown(f"Nyomja meg a gombot, hogy a megrendelését elküldje nekünk.")
        #st.markdown(f"Eddig ennyiszer nyomta meg a gombot: {st.session_state.button_press_counter}")
        #st.session_state.button_press_counter += 1
        #st.markdown("Ha megnyomja a gombot, és nem lát semmilyen egyéb üzenetet, ez alatt a mondat alatt, akkor nyomja meg a gombot újra.")
    with col2:
        st.markdown("Ha valami kérdése van, kérjük keressen minket bizalommal a következő elérhetőségeken:")
        st.markdown("Email: info@cleango.hu")
        st.markdown("Telefon: +36 30 141 5100")

    if st.session_state['button_press_counter'] == 1:
        st.session_state.button_press_counter = 0
    
        with st.spinner("Megrendelés elküldése folyamatban..."):
            st.session_state.session_counter = 0
            with col1:
                # some checks to see if the form is filled out correctly
                error_counter = 0

                if (st.session_state.szamlazasi_info_radio == "Egyéb") or (st.session_state.szamlazasi_info_radio == "Add meg a számlázási cimet"):
                    if len(st.session_state.szamlazasi_infok) < 3:
                        st.warning("Kérjük adja meg a számlázási információkat!")
                        error_counter += 1

                if len(st.session_state.number_plate) < 1:
                    st.warning("Kérjük adja meg a rendszámot!")
                    error_counter += 1
                
                if len(st.session_state.auto_markak_tipusok) < 1:
                    st.warning("Kérjük adja meg az autó márkáját és típusát!")
                    error_counter += 1

                if (st.session_state.helyszin == 'Egyéb') | (st.session_state.helyszin == "Adja meg a mosás helyét!"):
                    if len(st.session_state.helyszin) < 3:
                        st.warning("Kérjük adja meg a mosás helyét!")
                        error_counter += 1
                
                # chech email_user must contain @ and .
                if st.session_state.email_user.find("@") == -1:
                    st.warning("Kérjük adjon meg egy valós e-mail címet!")
                    error_counter += 1

                # chech email_user must contain @ and .
                if st.session_state.email_user.find(".") == -1:
                    st.warning("Kérjük adjon meg egy valós e-mail címet!")
                    error_counter += 1
                    
                # check email_user must not contain space
                if " " in st.session_state.email_user:
                    st.warning("Kérjük, ne használjon szóközt az e-mail cimben!")
                    error_counter += 1

                # chech if extrak is greater than 1
                if len(st.session_state.extrak) > 1:
                    # if extrak contains 'nem kérek extrát' then show warning
                    if 'nem kérek extrát' in st.session_state.extrak:
                        st.warning("Ha nem kért extrát, akkor ne válasszon ki más extrát.")
                        error_counter += 1
                
                if len(st.session_state.extrak) < 1:
                    st.warning("Kérjük válasszon ki legalább egy extrát, vagy valassza ki hogy nem kér extrát!")
                    error_counter += 1

                if error_counter == 0:
                    megjegyzes = st.session_state.megjegyzes_text_area.replace('\n', '')

                    answer_dict = {
                        "username": st.session_state.username,
                        "email_user": st.session_state.email_user,
                        "telefon": st.session_state.telefon,
                        "number_plate": st.session_state.number_plate,
                        "auto_markak_tipusok": st.session_state.auto_markak_tipusok,
                        "helyszin": st.session_state.helyszin,
                        "mosas_datum_ido": st.session_state.mosas_datum_ido,
                        "alapszolg": st.session_state.alapszolg,
                        "extrak": st.session_state.extrak,
                        "nev": st.session_state.nev,
                        "szamlazasi_infok": st.session_state.szamlazasi_infok,
                        "megjegyzes": megjegyzes
                    }

                    answer_dict_str = str(answer_dict)

                    email_body_to_us = 'Új mosás rendelés érkezett a B2B rendszerén keresztül!</p> <br><br> Ügyfél név: <br> {} <br><br> Mosandó autó: <br> Rendszám: {} <br> Autómárka és típus: {} <br><br> Mosás helyszín: <br> {} <br> Mosás időpontja: {} <br><br> Milyen mosást szerente rendelni? <br> {}, <br> Extrák: <br> {} <br><br>Kapcsolat: <br> {} <br> {}, {} <br><br> Számlázási információk: <br> {} <br><br> Megjegyzés: <br> {} <br>'.format(
                        st.session_state.username, st.session_state.number_plate, st.session_state.auto_markak_tipusok, st.session_state.helyszin, st.session_state.mosas_datum_ido,
                        st.session_state.alapszolg, st.session_state.extrak, st.session_state.nev, st.session_state.email_user, st.session_state.telefon, st.session_state.szamlazasi_infok, megjegyzes)
                    email_body_to_user = 'Köszönjük megrendelését a CleanGo - B2B rendszerén keresztül! Rendelését megkaptuk.</p> <br><br>Ez egy automatikusan generált email, kérjük ne válaszoljon rá!<br><br> Mergrendelő felhasználó neve: <br> {} <br><br> Mosandó autó: <br> Rendszám: {} <br> Autómárka és típus: {} <br><br> Mosás helyszín: <br> {} <br> Mosás időpontja: {} <br><br> Milyen mosást szerente rendelni? <br> {}, <br> Extrák: <br> {} <br><br>Kapcsolat: <br> {} <br> {}, {} <br><br> Számlázási információk: <br> {} <br><br> Megjegyzés: <br> {} <br><br><br> Ha a autómosását le szeretné mondani vagy másik időpontra foglalná át kérem vegye fel a kapcsolatot velünk emailben: info@cleango.hu vagy telefonon: +36301415100 <br><br>'.format(
                        st.session_state.username, st.session_state.number_plate, st.session_state.auto_markak_tipusok, st.session_state.helyszin, st.session_state.mosas_datum_ido,
                        st.session_state.alapszolg, st.session_state.extrak, st.session_state.nev, st.session_state.email_user,
                        st.session_state.telefon, st.session_state.szamlazasi_infok, megjegyzes)

                    conn = create_connection()
                    cursor = conn.cursor()
                    # I have these columns in the table: id, name, email, telephone_number, dob, questions, created_at, updated_at.
                    # The id and the created_at and updated_at columns are automatically filled by the database.
                    insert_query = """INSERT INTO cleango.bi_b2b_orders_registration (username, nev, email_user, mosas_datum_ido, answer_text) VALUES  ('{}', '{}', '{}', '{}', '{}')""".format(
                        st.session_state.username,
                        st.session_state.nev,
                        st.session_state.email_user,
                        st.session_state.mosas_datum_ido,
                        answer_dict_str.replace("'", "''")
                    )
                    cursor.execute(insert_query)
                    # Commit the changes and close the cursor and the database connection
                    conn.commit()
                    cursor.close()
                    conn.close()
                        
                    # send the email to CleanGo
                    # for email_adress_to_us in email_list_to_us:
                    #     try:
                    #         send_email(email_adress_to_us, email_subject, email_body_to_us)
                    #         st.write("Megrendelését a CleanGo megkapta. A megrendelését a lehető leghamarabb feldolgozzuk.")
                    #     except:
                    #         st.write("Hoppá valami hiba történt. A megrendelését a CleanGo nem kapta meg.")
                        
                    # send the email to the user
                    try:
                        #send_email(email_user, "CleanGo - B2B Rendelés Visszaigazolás", email_body_to_user)
                        st.success("Köszünjük, megrendelését a CleanGo sikeresen megkapta. A megrendelését a lehető leghamarabb feldolgozzuk.")
                        st.markdown("A megrendelési visszaigazolást az alábbi megadott email címre is elküldtük.")
                        st.markdown(" {}".format(st.session_state.email_user))
                        st.markdown("Az e-mail 5 percen belül érkezik meg (nem azonnal).")
                        st.markdown("Kérjük ellenőrizze a spam mappát is, mert sokszor oda kerül a visszaigazolás!")
                    except:
                        st.write("Hoppá valami hiba történt. A visszaigazolást nem tudtuk tudtuk elküldeni az alább megadott emailcimre!")
                        st.write("{}".format(st.session_state.email_user))
                    
                    try:
                        # send the slack message to the selected channel
                        slacbot_token_str = st.secrets['slackbot']['token']
                        client = WebClient(token=slacbot_token_str)
                        string_to_send_with_link = f"""B2B rendeles erkezett. Az alabbi felhaszanlotol: {st.session_state.username}. Tovabbi informacio itt: https://cleango-dashboard.streamlit.app/B2B_orders"""
                        client.chat_postMessage(channel="#"+"b2b_rendelo_felulet", text=string_to_send_with_link)
                    except:
                        print("Slack message sending error")

elif st.session_state.authentication_status == False:
    with col1:
        st.error('Username/password is incorrect')
elif st.session_state.authentication_status == None:
    with col1:
        st.warning('Please enter your username and password')
        st.write("If you don't have an account, please contact us at: info@cleango.hu")
        st.write("Or call us at: +36 30 141 5100")