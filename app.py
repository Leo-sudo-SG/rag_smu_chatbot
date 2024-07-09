
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import create_history_aware_retriever
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_pinecone import PineconeVectorStore
from langsmith import Client
from langchain_community.chat_message_histories import StreamlitChatMessageHistory
from firebase_admin import credentials, auth
from database import init_db, connect_db, register_user, save_chat_to_db, save_info_to_db, save_kmu_summary_to_db
import streamlit as st
import streamlit_authenticator as stauth
import uuid
import os
import random
import time
import firebase_admin

PINECONE_API_KEY=os.environ['PINECONE_API_KEY']
LANGCHAIN_TRACING_V2=os.environ['LANGCHAIN_TRACING_V2']
LANGCHAIN_ENDPOINT=os.environ['LANGCHAIN_ENDPOINT']
LANGCHAIN_API_KEY=os.environ['LANGCHAIN_API_KEY']
LANGCHAIN_PROJECT=os.environ['LANGCHAIN_PROJECT']
OPENAI_API_KEY=os.environ['OPENAI_API_KEY']


#from chatbot import init_chatbot
client = Client()

if not firebase_admin._apps:
    firebase_secrets=st.secrets["firebase"]

    firebase_credentials={
         "type":firebase_secrets["type"],
         "project_id":firebase_secrets["project_id"],
         "private_key_id":firebase_secrets["private_key_id"],
         "private_key":firebase_secrets["private_key"].replace("\\n","\n"),
         "client_email":firebase_secrets["client_email"],
         "client_id":firebase_secrets["client_id"],
         "auth_uri":firebase_secrets["auth_uri"],
         "token_uri":firebase_secrets["token_uri"],
         "auth_provider_x509_cert_url":firebase_secrets["auth_provider_x509_cert_url"],
         "client_x509_cert_url":firebase_secrets["client_x509_cert_url"]
    }
    cred = credentials.Certificate(firebase_credentials)
    firebase_admin.initialize_app(cred)

# Set title
st.title("FragenFabrik")
st.subheader("Willkommen in der FragenFabrik. Diese Anwendung wird Ihnen helfen, Interviews zu führen, und so Möglichkeiten für Ihre Idee zu erkunden.")

#tab1, tab2 = st.tabs(["Beantworten Sie einige Fragen über Ihre Idee.", "Überprüfen Sie Ihre Angaben."])

# Initialize session state variables
if 'email' not in st.session_state:
    st.session_state.email= ""
if 'product' not in st.session_state:
    st.session_state.product = ""
if 'stage' not in st.session_state:
    st.session_state.stage = ""
if 'name' not in st.session_state:
    st.session_state.name = ""
if 'target' not in st.session_state:
    st.session_state.target = ""
if 'user' not in st.session_state:
    st.session_state.user = ""
if 'company' not in st.session_state:
    st.session_state.company = ""
if 'ready' not in st.session_state:
    st.session_state.ready = False
if 'service_or_product' not in st.session_state:
    st.session_state.service_or_product = ""
if 'age_values' not in st.session_state:
    st.session_state.age_values = ["notready"]
if 'numberquestions' not in st.session_state:
     st.session_state.numberquestions = 5
if "input_disabled_name" not in st.session_state:
    st.session_state.input_disabled_name = False
if "input_disabled_product" not in st.session_state:
    st.session_state.input_disabled_product = False
if "input_disabled_target" not in st.session_state:
    st.session_state.input_disabled_target = False
if "input_disabled_user" not in st.session_state:
    st.session_state.input_disabled_user = False
if "input_disabled_company" not in st.session_state:
    st.session_state.input_disabled_company = False
if "messages" not in st.session_state:
    st.session_state.messages = []
# Session state variable to track the current page
if 'page' not in st.session_state:
    st.session_state.page = "page1"
if "selected_language" not in st.session_state:
     st.session_state.selected_language = ""
if 'ready_interview' not in st.session_state:
    st.session_state.ready_interview = False
if "answers" not in st.session_state:
     st.session_state.answers=[]
if "sum_prompt" not in st.session_state:
     st.session_state.sum_prompt=""

def disable_input_name():
    st.session_state.input_disabled_name = True

def disable_input_product():
    st.session_state.input_disabled_product = True

def disable_input_target():
    st.session_state.input_disabled_target = True

def disable_input_company():
    st.session_state.input_disabled_company = True

def disable_input_user():
    st.session_state.input_disabled_user = True

def agechange():
    st.session_state.age_values = ["ready"]

def stage_conv(session_state):  
                        if(session_state ==1):
                            st.session_state.stage="Ideation"
                        elif(session_state ==2):
                            st.session_state.stage="Product Definition"
                        elif(session_state ==3):
                            st.session_state.stage="Prototyping"
                        elif(session_state ==4):
                            st.session_state.stage="Initial Design"
                        elif(session_state ==5):
                            st.session_state.stage="Validation & Testing"
                        elif(session_state ==6):
                            st.session_state.stage="Commercialization"
                        elif(session_state==None):
                             st.session_state.stage="Not specified"

# Session state variable to track the current page
if 'page' not in st.session_state:
    st.session_state.page = "page1"

# Page 1 content
def page1():
    st.title("Anmeldung")

    email = st.text_input("Email", autocomplete="off")
    password = st.text_input("Passwort", type="password")
    col1, col2 = st.columns(2)
    with col1: login_button = st.button("Melden Sie sich an.")
    #with col2: 
    st.subheader("**Neu hier?**")
    st.write("Schön, dass Sie den Weg zu uns gefunden haben!")
    signup_button = st.button("Registrieren Sie sich.")

    # Registrierung
    if signup_button:
        st.session_state.page = "signup_page"

    # Anmeldung
    if login_button:
        try:
            user = auth.get_user_by_email(email)
            st.success(f"Successfully logged in as {user.email}")
            st.session_state.email=email
            st.session_state.page = "page2"
        except auth.UserNotFoundError:
            st.error("User not found or incorrect credentials")

# Function to sign up a user with email and password
def sign_up_with_email_password(email, password):
    try:
        # Create user using Firebase Authentication
        user = auth.create_user(email=email, password=password)
        st.success(f"User wurde erfolgreich erstellt.")
        return user
    except Exception as e:
        # Handle error if user creation fails
        st.error(f"Fehler beim Erstellen des Users: {e}")
        return None

def signup_page():
    st.title("Registrierung")
    # Input fields for email, password, and confirm password
    email = st.text_input("Email",autocomplete="off")
    password = st.text_input("Passwort", type="password", placeholder="Wählen Sie mindestens sechs Zeichen für Ihr Passwort.")
    confirm_password = st.text_input("Bestätigen Sie Ihr Passwort", type="password")

    col1, col2 = st.columns([0.15,0.85])
    with col1: but_su = st.button("Sign Up")
    with col2: but_zu = st.button("Zurück")

    # Sign-up button
    if but_su:
        # Check if passwords match
        if password != confirm_password:
            st.error("Passwörter stimmen nicht überein.")
        else:
            # Call sign_up_with_email_password function
            user = sign_up_with_email_password(email, password)
            st.session_state.email=email
            if user:
                # Additional logic after successful sign-up
                pass

    if but_zu: st.session_state.page = "page1"
         
# Page 2 content
def page2():
    
    with st.chat_message("ai", avatar=":material/psychology:"):
            st.write("Hallo, ich hoffe, es geht Ihnen gut! Wir werden jetzt einige Informationen über Sie und Ihre Idee sammeln, damit wir die bestmöglichen Interviews für Sie erstellen können.")
                                                
    with st.container():  
            st.subheader("Grundlegende Informationen")
            # Display chat messages from history on app rerun
            for message in st.session_state.messages:
                with st.chat_message(message["role"], avatar=":material/mood:" if message["role"] == "user" else ":material/psychology:"):
                    st.markdown(message["content"])

    with st.container():
            placeholder = st.empty()

            if not st.session_state.input_disabled_user:
                with placeholder.container():
                    st.write("**Lassen Sie uns bei Ihnen beginnen.**")
                    name_input = st.chat_input("Wie heißen Sie?")
                    notsure1 = st.checkbox("Keine Angabe.", key="box1")

                if notsure1:
                    st.session_state.user = "Keine Angabe."
                    placeholder.empty()

                if name_input:
                    placeholder.empty()
                    with st.chat_message("user", avatar=":material/mood:"):
                        st.markdown(name_input)
                    st.session_state.user = name_input
                    st.session_state.messages.append({"role": "user", "content": name_input})
                    disable_input_user()
                    
                    def response_generator1(prompt1):
                        response = random.choice(
                            [
                                "Herzlich willkommen "+prompt1+"!",
                                "Hey " +prompt1+", schön, dass Sie hier sind.",
                                "Hallo  " +prompt1+", herzlich willkommen bei unserem Interview Bot.",
                            ]
                        )
                        for word in response.split():
                            yield word + " "
                            time.sleep(0.06)
                    
                    with st.chat_message("ai", avatar=":material/psychology:"):
                        response = st.write_stream(response_generator1(name_input))

                    st.session_state.messages.append({"role": "ai", "content": response})
            
            if not st.session_state.input_disabled_company and st.session_state.user:
                placeholder2 = st.empty()
                with placeholder2.container():
                    st.write("**Weiter geht es mit Ihrer Firma:**")
                    company = st.chat_input("Wie heißt die Firma, bei der Sie arbeiten?")
                    notsure2 = st.checkbox("Keine Angabe.", key="box2")

                if notsure2:
                    st.session_state.company = "Keine Angabe."
                    placeholder2.empty() # entferne die chatbox

                if company:
                    placeholder2.empty() # entferne die chatbox
                    with st.chat_message("user", avatar=":material/mood:"):
                        st.markdown(company)
                    st.session_state.company = company
                    st.session_state.messages.append({"role": "user", "content": company})
                    disable_input_company()
                    
                    def response_generator1(prompt1):
                        if st.session_state.user == "Keine Angabe.":
                            response = "Sie arbeiten also bei "+ prompt1
                        else:
                            response = random.choice(
                                [
                                    "Okay, "+st.session_state.user+ ", Sie arbeiten also bei "+ prompt1+"!",
                                    st.session_state.user+" von " +prompt1+", schön, dass Sie hier sind.",
                                ]
                            )
                        for word in response.split():
                            yield word + " "
                            time.sleep(0.06)
                    
                    with st.chat_message("ai", avatar=":material/psychology:"):
                        response = st.write_stream(response_generator1(company))

                    st.session_state.messages.append({"role": "ai", "content": response})
            

            # Collect the product name
            if not st.session_state.input_disabled_name and st.session_state.company:
                placeholder3 = st.empty()

                with placeholder3.container():
                    st.write("**Erzählen Sie mir ein bisschen mehr über Ihre Idee:**")
                    name_input = st.chat_input("Haben Sie schon einen Namen im Kopf?")
                    notsure3 = st.checkbox("Nein, noch nicht.", key="box3")

                if notsure3:
                    st.session_state.name = "Keine Angabe."
                    placeholder3.empty() # entferne die chatbox
                    #det_info['prod_name']="Keine Angabe"

                if name_input:
                    placeholder3.empty() # entferne die chatbox
                    with st.chat_message("user", avatar=":material/mood:"):
                        st.markdown(name_input)
                    st.session_state.name = name_input
                    st.session_state.messages.append({"role": "user", "content": name_input})
                    #det_info["prod_name"]= name_input
                    disable_input_name()
                    
                    def response_generator1(prompt1):
                        response = random.choice(
                            [
                                "Okay, "+prompt1+", damit können wir arbeiten.",
                                prompt1+", das klingt nach einem guten Namen.",
                                "Sehr kreativ -  " +prompt1+", wie sind Sie da überhaupt drauf gekommen?",
                            ]
                        )
                        for word in response.split():
                            yield word + " "
                            time.sleep(0.06)
                    
                    with st.chat_message("ai", avatar=":material/psychology:"):
                        response = st.write_stream(response_generator1(name_input))

                    st.session_state.messages.append({"role": "ai", "content": response})
            
            # Collect the product description
            placeholder4 = st.empty()
            if st.session_state.ready_interview == False:
                with placeholder4.container():
                    if st.session_state.name and st.session_state.name != "Keine Angabe.":
                            st.write("Worum handelt es sich bei Ihrer Idee: Einem Produkt oder eine Dienstleistung?")
                            produktname = st.session_state.name
                            st.session_state.service_or_product = st.radio(label=produktname+" ist ein:",options=["Produkt","Dienstleistung","Ich weiss es noch nicht."], index=None)
                    elif st.session_state.name and st.session_state.name == "Keine Angabe.":
                            st.write("Worum handelt es sich bei Ihrer Idee: Einem Produkt oder eine Dienstleistung?")
                            produktname = st.session_state.name
                            st.session_state.service_or_product = st.radio(label="Es ist ein:",options=["Produkt","Dienstleistung","Ich weiss es noch nicht."], index=None)
                        
            # Collect the target group description
            
            if st.session_state.ready_interview == False and (st.session_state.service_or_product == "Produkt" or st.session_state.service_or_product == "Dienstleistung" or st.session_state.service_or_product == "Ich weiss es noch nicht."):
                placeholder4.empty()

                with st.container():
                    st.subheader("Zielgruppe")
                
                    placeholder6 = st.empty()
                    with placeholder6.container():
                            values = st.slider(
                                "In welchem Alter befindet sich Ihre Zielgruppe?",
                                0, 100, (25, 75))
                            st.write("Alterstruktur:", values)
                    
                    st.session_state.age_values.insert(0,values[0])
                    st.session_state.age_values.insert(1,values[1])
                    #det_info['target_group']= str(st.session_state.age_values[0]) + "-" + str(st.session_state.age_values[1])

                    notsure4 = st.checkbox("Ich bin mir noch nicht sicher.", key="box4")
                        
                    if notsure4:
                            placeholder6.empty()
                            st.session_state.age_values.clear()
                            st.session_state.age_values.insert(0,"Keine Angabe.")
                            #det_info['target_group']='Keine Angabe.'
                        
                    st.subheader("Momentaner Entwicklungsstand")
                    st.write("**Wo in der Entwicklung befinden Sie sich gerade?**")
                               
                
                    placeholder5 = st.empty()
                    with placeholder5.container():
                        # Labels for the slider
                        col1, col2, col3, col4, col5, col6 = st.columns(6)
                        with col1: st.write("Ideation")
                        with col2: st.write("Product Definition")  
                        with col3: st.write("Prototyping")
                        with col4: st.write("Initial Design")
                        with col5: st.write("Validation & Testing")
                        with col6: st.write("Commercialization")
                                
                        st.session_state.stage = st.slider(
                            label="Wir sind gerade in...",
                            min_value=1,
                            max_value=6,
                            key="current_stage",
                            step=1,
                            help=(
                                "1) **Ideation**: Die erste Phase des Produktentwicklungsprozesses beginnt mit der Generierung neuer Produktideen. Dies ist die Phase der Produktinnovation, in der Sie Produktkonzepte basierend auf Kundenbedürfnissen, Konzepttests und Marktforschung brainstormen.\n"
                                "2) **Product Definition**: Dies wird auch als Abgrenzung oder Konzeptentwicklung bezeichnet und konzentriert sich auf die Verfeinerung der Produktstrategie und die gründliche Definition Ihres Produkts.\n"
                                "3) **Prototyping**: Während dieser Phase wird Ihr Team intensiv recherchieren und das Produkt dokumentieren, indem ein detaillierterer Geschäftsplan erstellt und das Produkt konstruiert wird.\n"
                                "4) **Initial Design**: Die Projektbeteiligten arbeiten zusammen, um ein Mockup des Produkts basierend auf dem Prototyp des Minimum Viable Product (MVP) zu erstellen. Das Design sollte mit der Zielgruppe im Hinterkopf erstellt werden und die wichtigsten Funktionen Ihres Produkts ergänzen.\n"
                                "5) **Validation & Testing**: Um mit einem neuen Produkt live zu gehen, müssen Sie es zuerst validieren und testen. Dies stellt sicher, dass jeder Teil des Produkts - von der Entwicklung bis zum Marketing - effektiv funktioniert, bevor es der Öffentlichkeit zugänglich gemacht wird.\n"
                                "6) **Commercialization**: Nun ist es an der Zeit, Ihr Konzept zu kommerzialisieren, was den Start Ihres Produkts und die Implementierung auf Ihrer Website umfasst."
                            )
                        )
        
                        notsure5 = st.checkbox("Keine Angabe.", key="box5")
                        
                        if notsure5:
                            st.session_state.stage = None
                            placeholder5.empty()
                            placeholder6.empty()
                            #det_info['dev_status']='Keine Angabe'

                    # Show which phase they chose
                    with st.chat_message("ai", avatar=":material/psychology:"):
                                if st.session_state.stage == 1: 
                                    st.write("Super, Sie sind also gerade in der **Ideation** Phase.")
                                    #det_info['dev_status']="Ideation"
                                if st.session_state.stage == 2: 
                                    st.write("Super, Sie sind also gerade in der **Product Definition** Phase.")
                                    #det_info['dev_status']="Product Definition"
                                if st.session_state.stage == 3: 
                                    st.write("Super, Sie sind also gerade in der **Prototyping** Phase.")
                                    #det_info['dev_status']="Prototyping"
                                if st.session_state.stage == 4: 
                                    st.write("Super, Sie sind also gerade in der **Initial Design** Phase.")
                                    #det_info['dev_status']="Initial Design"
                                if st.session_state.stage == 5: 
                                    st.write("Super, Sie sind also gerade in der **Validation & Testing** Phase.")
                                    #det_info['dev_status']="Validation & Testing"
                                if st.session_state.stage == 6: 
                                    st.write("Super, Sie sind also gerade in der **Commercialization** Phase.")
                                    #det_info['dev_status']="Commercialization"

                    placeholder7 = st.empty()
                    with placeholder7.container():
                        but = st.button("Weiter gehts.", key="weiter")
                        if but:
                            placeholder5.empty()
                            placeholder6.empty()
                            st.session_state.ready_interview = True
                            placeholder7.empty()
            
            if st.session_state.ready_interview == True:
                with st.container():
                        st.subheader("Nun zu den Interviews:") 
                        st.write("Wie viele Fragen möchten Sie Ihren Befragten stellen?")
                        # Auswahl der Fragenanzahl
                        st.session_state.numberquestions = st.slider(
                            label="**Anzahl Fragen**", 
                            min_value=1,
                            max_value=15,
                            value=st.session_state.numberquestions,
                            step=1,
                            key="anzahlfragen",
                            help=("In der Wissenschaft werden zwischen 5 und 10 Fragen empfohlen."))
                        #det_info['num_ques']=st.session_state.numberquestions
                        
                        dauer = str(st.session_state.numberquestions*6)
                        # man kann pro Frage mit 6 min rechnen: https://sozmethode.hypotheses.org/132
                        st.write("Damit wird Ihr Interview in etwa "+ dauer + " Minuten dauern.")
                        
                        st.write("**Auf welcher Sprache sollen die Interviews durchgeführt werden?**")

                        # Liste der häufigsten Sprachen in Europa, alphabetisch geordnet
                        languages = sorted([
                            "Russisch", "Deutsch", "Französisch", "Englisch", "Italienisch", "Spanisch", "Ukrainisch", "Polnisch", "Rumänisch", "Niederländisch",
                            "Griechisch", "Ungarisch", "Portugiesisch", "Tschechisch", "Schwedisch", "Bulgarisch", "Serbisch", "Kroatisch", "Slowakisch", "Dänisch",
                            "Finnisch", "Norwegisch", "Litauisch", "Slowenisch", "Lettisch", "Estnisch", "Mazedonisch", "Albanisch", "Isländisch",
                            "Irisch", "Maltesisch", "Bosnisch", "Walisisch", "Weißrussisch", "Katalanisch"
                        ])

                        # Erstelle eine Auswahlbox
                        st.session_state.selected_language = st.selectbox(
                            "Wählen Sie eine Sprache",
                            languages,
                            index = None
                        )
                        #det_info['lang_ques']=st.session_state.selected_language
                        # Zeige die ausgewählte Sprache an
                        st.write(f"Ihre Interviews werden in **{st.session_state.selected_language}** durchgeführt werden.")

                        if st.session_state.selected_language != "":
                            st.subheader("Wir danken Ihnen für die Informationen. Überprüfen Sie nun die von Ihnen angegebenen Daten auf ihre Korrektheit und senden Sie sie ab!")
                            # Button to switch to Prüfpage 
                            but = st.button("Überprüfen Sie Ihre Angaben.", key="pruefung")
                            if but:
                                st.session_state.page = "page3"
                                
                                
                
# Page 3 content: Overview of collected information
def page3():
        with st.container():
            # Name und Firma
                st.subheader("Diese Information haben Sie uns bisher bereitgestellt.")
                if st.session_state.user != "Keine Angabe." and st.session_state.company != "Keine Angabe.":
                    st.write("Sie heißen **"+ st.session_state.user + "** und arbeiten bei **" + st.session_state.company + "**.")
                        
                if st.session_state.user != "Keine Angabe." and st.session_state.company == "Keine Angabe.":
                    st.write("Sie heißen **"+ st.session_state.user +"**.")
                        
                if st.session_state.user == "Keine Angabe." and st.session_state.company != "Keine Angabe.":
                    st.write("Sie arbeiten bei **"+ st.session_state.company +"**.")
                        
                if st.session_state.user == "Keine Angabe." and st.session_state.company == "Keine Angabe.":
                    st.write("Sie haben uns keine Information zu Ihnen selbst zukommen lassen.")

            # Vorhaben        
                if st.session_state.name != "Keine Angabe.":
                    st.write("Der **Name** für Ihr Vorhaben ist " + st.session_state.name)
                else: st.write("Sie haben noch keinen **Namen** für Ihr Vorhaben.")
            
            #Zielgruppe
                if st.session_state.age_values[0] != "Keine Angabe.":
                        st.write("Ihre **Zielgruppe** ist zwischen "+str(st.session_state.age_values[0])+ " und "+str(st.session_state.age_values[1])+" Jahren alt.")
                        if st.session_state.stage == 1: st.write("Sie sind gerade in der **Ideation** Phase.")
                        if st.session_state.stage == 2: st.write("Sie sind gerade in der **Product Definition** Phase.")
                        if st.session_state.stage == 3: st.write("Sie sind gerade in der **Prototyping** Phase.")
                        if st.session_state.stage == 4: st.write("Sie sind gerade in der **Initial Design** Phase.")
                        if st.session_state.stage == 5: st.write("Sie sind gerade in der **Validation & Testing** Phase.")
                        if st.session_state.stage == 6: st.write("Sie sind gerade in der **Commercialization** Phase.")
                else: 
                            st.write("Sie sind sich noch nicht über die Alterstruktur Ihrer **Zielgruppe** bewusst.")

                if st.session_state.service_or_product == "Ich weiss es noch nicht.":
                            st.write("Sie sind sich noch nicht darüber bewusst, ob es sich um ein Produkt oder eine Dienstleistung handelt.")
                if st.session_state.service_or_product == "Produkt":
                            st.write("Es handelt sich um ein **" + st.session_state.service_or_product+"**.")
                if st.session_state.service_or_product == "Dienstleistung":
                            st.write("Es handelt sich um eine **" + st.session_state.service_or_product+"**.")
                
                dauer = str(st.session_state.numberquestions * 6)
                st.write("In Ihren Interviews werden **" +str(st.session_state.numberquestions)+" Fragen** gestellt werden.")
                st.write("Damit werden diese voraussichtlich **"+ dauer +" Minuten** dauern.")
                
                st.write(f"Ihre Interviews werden in **{st.session_state.selected_language}** durchgeführt werden.")

                col1, col2 = st.columns([0.3,0.7])
                
                with col1:
                    but_los = st.button("Weiter gehts!", key="aufgehts")
                    if but_los:
                        st.session_state.page = "page4"
                        stage_conv(st.session_state.stage)
                        if "det_info" not in st.session_state:
                            st.session_state.det_info={ 'product_name':st.session_state.name,
                                                        'product_type':st.session_state.service_or_product,
                                                        'target_group':str(st.session_state.age_values[0])+"-"+str(st.session_state.age_values[1]),
                                                        'dev_status':st.session_state.stage,
                                                        'num_ques':st.session_state.numberquestions,
                                                        'lang_ques':st.session_state.selected_language
                            }
                        

                with col2: 
                    but_edit = st.button("Ich möchte meine Daten noch einmal anpassen.", key="edit")
                    if but_edit:
                        st.session_state.page = "editinfos"


def editinfos():
    st.title("Bearbeiten Sie Ihre Angaben.")
    st.session_state.user = st.text_area("**Ihr Name**", value=st.session_state.user, height=20)
    st.session_state.company = st.text_area("**Ihre Firma**", value=st.session_state.company, height=20)
    st.session_state.name = st.text_area("**Ihr Produktname**", value=st.session_state.name, height=20)
    # Development Stage
    st.write("**Ihr momentaner Entwicklungsstand:**")
    # Labels for the slider
    
    beschriftungslider = st.container()
    with beschriftungslider:
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        with col1: st.write("Ideation")
        with col2: st.write("Product Definition")
        with col3: st.write("Prototyping")
        with col4: st.write("Initial Design")
        with col5: st.write("Validation & Testing")
        with col6: st.write("Commercialization")
                
    st.session_state.stage = st.slider(label="Wir sind gerade in...", min_value=1, max_value=6, value=st.session_state.stage, key="edit_current_stage", step=1, help="1) Ideation \n 2) Product definition\n 3) Prototyping\n 4) Initial design\n 5) Validation and testing\n 6) Commercialization")

    indexsop = 0
    if st.session_state.service_or_product == "Produkt": 
        indexsop = 0
    elif st.session_state.service_or_product == "Dienstleistung": 
        indexsop = 1
    else: indexsop = 2
    
    if st.session_state.name and st.session_state.name != "Keine Angabe.":
                st.write("**Worum handelt es sich bei Ihrer Idee: Einem Produkt oder eine Dienstleistung?**")
                produktname = st.session_state.name
                st.session_state.service_or_product = st.radio(label=produktname+" ist ein:",options=["Produkt","Dienstleistung","Ich weiss es noch nicht."],index=indexsop)
    # name kann nicht verwendet werden
    elif st.session_state.name and st.session_state.name == "Keine Angabe.":
                    st.write("**Worum handelt es sich bei Ihrer Idee: Einem Produkt oder eine Dienstleistung?**")
                    produktname = st.session_state.name
                    st.session_state.service_or_product = st.radio(label="Es ist ein:",options=["Produkt","Dienstleistung","Ich weiss es noch nicht."])
    
    if st.session_state.age_values[0] != "Keine Angabe.":
        col3, col4 = st.columns(2)
        with col3: 
            st.session_state.age_values[0] = st.text_area("**Ihre Zielgruppe ist zwischen**", value=str(st.session_state.age_values[0]), height=20)
        with col4:
            st.session_state.age_values[1] = st.text_area("**und**", value=str(st.session_state.age_values[1]), height=20)

    else:
        st.write("Sie haben keine Angaben zur Altersttruktur Ihrer Zielgruppe gemacht. Möchten Sie dies ändern?")
        change = st.checkbox("Ja.")
        if change: 
            col3, col4 = st.columns(2)
            with col3: 
                st.session_state.age_values[0] = st.text_area("**Ihre Zielgruppe ist zwischen**", value=str(st.session_state.age_values[0]), height=20)
            with col4:
                st.session_state.age_values[1] = st.text_area("**und**", value=str(st.session_state.age_values[1]), height=20)

        # Auswahl der Fragen
    st.session_state.numberquestions = st.slider(
                            label="**Anzahl Fragen**", 
                            min_value=1,
                            max_value=15,
                            value=st.session_state.numberquestions,
                            step=1,
                            key="anzahlfragen",
                            help=("In der Wissenschaft werden zwischen 5 und 10 Fragen empfohlen."))
                        
    dauer = str(st.session_state.numberquestions*6)
        # man kann pro Frage mit 6 min rechnen: https://sozmethode.hypotheses.org/132
    st.write("Damit wird Ihr Interview in etwa "+ dauer + " Minuten dauern.")
                        
    st.write("Die Interviews werden auf **"+st.session_state.selected_language+"** durchgeführt werden.")

        # Liste der häufigsten Sprachen in Europa, alphabetisch geordnet
    languages = sorted([
                            "Russisch", "Deutsch", "Französisch", "Englisch", "Italienisch", "Spanisch", "Ukrainisch", "Polnisch", "Rumänisch", "Niederländisch",
                            "Griechisch", "Ungarisch", "Portugiesisch", "Tschechisch", "Schwedisch", "Bulgarisch", "Serbisch", "Kroatisch", "Slowakisch", "Dänisch",
                            "Finnisch", "Norwegisch", "Litauisch", "Slowenisch", "Lettisch", "Estnisch", "Mazedonisch", "Albanisch", "Isländisch",
                            "Irisch", "Maltesisch", "Bosnisch", "Walisisch", "Weißrussisch", "Katalanisch"
                        ])

        # Erstelle eine Auswahlbox
    st.session_state.selected_language = st.selectbox(
                            "Wählen Sie eine Sprache",
                            languages,
                            index=languages.index(st.session_state.selected_language) if st.session_state.selected_language in languages else 0
                        )

    submitinfos = st.button("Weiter gehts!")
    if submitinfos:
        st.session_state.page = "page3"
        stage_conv(st.session_state.stage)
        if "det_info" not in st.session_state:
            st.session_state.det_info={ 'product_name':st.session_state.name,
                                        'product_type':st.session_state.service_or_product,
                                        'target_group':str(st.session_state.age_values[0])+"-"+str(st.session_state.age_values[1]),
                                        'dev_status':st.session_state.stage,
                                        'num_ques':st.session_state.numberquestions,
                                        'lang_ques':st.session_state.selected_language
                                    }
            
        
def load_retriever():
    index_name = "llm"
    embedding=OpenAIEmbeddings()
    vectorstore = PineconeVectorStore(index_name=index_name, embedding=embedding)
    retriever=vectorstore.as_retriever(
    search_kwargs={"namespace":"llm1_2", "k":2}
    )

    return retriever

# not used
def generate_quest(llm_chain,user_input):
     return llm_chain.stream({"input": user_input}, 
                             config={ "configurable": st.session_state['chat_id']},)["answer"]


def split_response(response):
     for word in response.split():
        yield word + " "
        time.sleep(0.06)

def load_det_info(info):
     
     ret=[
        f"The product name is: {info['product_name']}",
        f"The product type is: {info['product_type']}",
        f"The target group is age range: {info['target_group']}",
        f"The products developement status is: {info['dev_status']}",
        f"Approximate number of questions to be asked of the potential customer: {info['num_ques']}",
        f"The interview with the potential customer should be conducted in the following language: {info['lang_ques']}",          
     ]
     separator ="\n"
     s=separator.join(ret)
     return s
          

def create_prompt_template(det_info):
    prompt_parts = [
        f"The product name is: {det_info['product_name']}",
        f"The product type is: {det_info['product_type']}",
        f"The target group is age range: {det_info['target_group']}",
        f"The products developement status is: {det_info['dev_status']}",
        #f"Number of questions to be asked of the potential customer: {det_info['num_ques']}",
        #f"The interview with the potential customer should be conducted in the following language: {det_info['lang_ques']}",
        #f"Main features: {', '.join(product_info['features'])}"
    ]
    prompt_template = """
    Task:
    As a helpful AI interview bot, your goal is to obtain relevant information about a product/service idea by asking the most appropriate and precise questions possible.
    The aim of the interview is to gather as much detailed information as possible about the product/service. 
    
    Instructions:
    You talk to a product owner who has an idea for a product or service that has not yet been developed.
    The information you collect will later be used for user research and in particular for the user-centred development of the product/service.
    Conduct the entire interview in German. Be careful not to ask questions twice or repeat yourself.
    Make the interview interactive and add meaningful questions, for that use your common knowledge and extend it with the given questions from a questionaire.
    
    Useful questions:
    {context}

    If there is no suitable question, ask your own question. If an answer is very short or incomplete, ask a follow-up question. 
    The questions should not be asked all at once, but alternate with the user's answers.
    For answers that have nothing to do with the question asked, try to re-enter the interview with a new question. 
    End the interview after about 10-15 Questions.
    Once all the questions have been asked, ask the product owner if they would like to add any further information and respond to their answer.
    At the end also point out that the interview can be concluded by entering "exit".
    If the user does not enter any further information, answer any further input with "Please type "exit" to finish the interview.".
    Only create a summary if exit has been entered by the user.


    Always use the following information of the product/service to ask suitable questions.
    Product/Service information:
    """.join(prompt_parts)

    return prompt_template

def generate_link():
     base_url="http://localhost:8501"
     hidden_link=f"{base_url}?token={st.session_state['chat_id']}"
     return hidden_link

def interview():
    conn, c= connect_db(st.secrets["DATABASE_NAME"],st.secrets["DATABASE_USER"],st.secrets["DATABASE_PASSWORD"],st.secrets["DATABASE_HOST"])
    register_user(conn,c,st.session_state['chat_id'],st.session_state['email'])
    

    retriever = load_retriever()
    msgs = StreamlitChatMessageHistory(key="langchain_messages")

    model = ChatOpenAI(model_name="gpt-4o", temperature=0, streaming=True)
    contextualize_q_system_prompt="""Given a chat history and the latest user response
    which might reference context in the chat history, formulate a possible follow-up question that can be understood without the chat history."""
    contextualize_q_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human","{input}")
        ]
    )

    history_aware_retriever = create_history_aware_retriever(
        model, retriever, contextualize_q_prompt
    )

    interview_system_prompt = create_prompt_template(st.session_state.det_info)

    interview_prompt= ChatPromptTemplate.from_messages(
        [
            ("system", interview_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human","{input}")
    
        ]
    )

    interview_chain = create_stuff_documents_chain(model, interview_prompt)
    rag_chain = create_retrieval_chain(history_aware_retriever,interview_chain)

    conversational_rag_chain = RunnableWithMessageHistory( 
        rag_chain,
        lambda session_id: msgs,
        input_messages_key="input",
        history_messages_key="chat_history",
        output_messages_key="answer"
    )

    if len(msgs.messages)==0:
        save_info_to_db(conn,c,st.session_state['chat_id'],load_det_info(st.session_state.det_info))

        first_prompt="Please welcome me and give me short instruction on what to do and what to expect."
        config = {"configurable": {"session_id": st.session_state['chat_id']}}
        response = conversational_rag_chain.invoke({"input": first_prompt}, config)['answer']
        answer={"role":"ai", "input":response}
        st.session_state.answers.append(answer)

    for answer in st.session_state.answers:
        with st.chat_message(answer["role"]):
            st.markdown(answer["input"])


    if prompt := st.chat_input("Antworte hier..."):
        config = {"configurable": {"session_id": st.session_state['chat_id']}}
        
        if "exit" in prompt:
            st.session_state.page="page5"
            sum_prompt="Give me a summary over the interview."
            st.session_state.sum_prompt=conversational_rag_chain.invoke({"input": sum_prompt}, config)['answer']
            save_kmu_summary_to_db(conn, c, st.session_state['chat_id'], st.session_state['sum_prompt'])
            st.rerun()
            
            
        st.session_state.answers.append({"role": "human", "input": prompt})

        with st.chat_message("human"):
            st.markdown(prompt)

        with st.spinner("Ich überlege mir eine Frage..."):   
            response = conversational_rag_chain.invoke({"input": prompt}, config)['answer']     
            
        # Note: new messages are saved to history automatically by Langchain during run
        with st.chat_message("ai"):
            st.write_stream(split_response(response))
        answer = {"role": "ai", "input": response}
        st.session_state.answers.append(answer)
        save_chat_to_db(conn, c, st.session_state['chat_id'], f"User: {prompt} AI: {response}")
    


    

    

def page4():
    st.subheader("Wilkommen zum Chatbot!")
    # Generate a unique chat ID for each session
    if 'chat_id' not in st.session_state:
        st.session_state.chat_id = str(uuid.uuid4())
    
    interview()


def page5():
    with st.container():
        st.subheader("Zusammenfassung Ihres Interviews:")
        link="[Chat-Bot]"+"("+generate_link()+")"
        st.write("Klicken Sie hier um den Interview-Bot für Ihr Produkt aufzurufen:")
        st.markdown(link, unsafe_allow_html=True)
        st.markdown(st.session_state.sum_prompt)


    
if st.session_state.page == "page1":
    page1()
elif st.session_state.page == "page2":
    page2()
elif st.session_state.page == "page3":
    page3()
elif st.session_state.page == "page4":
    page4()
elif st.session_state.page == "page5":
     page5()
elif st.session_state.page == "editinfos":
    editinfos()
elif st.session_state.page == "signup_page":
    signup_page()
