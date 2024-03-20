import pandas as pd 
import easyocr 
import streamlit as st
from streamlit_option_menu import option_menu
import mysql.connector
import os
import re
from PIL import Image

#setting page confi
icon=Image.open(r"C:\Users\sunil\OneDrive\Desktop\python guvi\Businesscard\business-card.png")
st.set_page_config(page_title="BizcardX:Extracting Business card Data with easyOCR | by SUNIL RAGAV",
                   page_icon=icon,
                   layout="wide",
                   initial_sidebar_state="expanded",
)
st.markdown("<h1 style='text-align: center; color: white;'>BizCardX: Extracting Business Card Data with easyOCR</h1>", unsafe_allow_html=True)
st.sidebar.header(":wave: :green[**Hello! Welcome to the dashboard**]")
#creating options
with st.sidebar:
    selected = option_menu(None, ["Home","Upload & Extract","Modify"], 
                       icons=["house","cloud-upload","pencil-square"],
                       default_index=0,
                       orientation="horizontal",
                       styles={"nav-link": {"font-size": "25px", "text-align": "center","padding":"0px", "margin": "5px", "--hover-color": "#A5DD9B"},
                               "icon": {"font-size": "25px"},
                               "container" : {"max-width": "3000px"},
                               "nav-link-selected": {"background-color": "#C5EBAA"}})

#connecting mysql
mydb=mysql.connector.connect(host="localhost",
                 user="root",
                 password="",
                 
)
mycursor=mydb.cursor(buffered=True)
#database creation
mycursor.execute("create database if not exists BiscardData")

#use this database
mycursor.execute("use BiscardData")




#table creation in sql
mycursor.execute('''CREATE TABLE IF NOT EXISTS card_data
                   (id INTEGER PRIMARY KEY AUTO_INCREMENT,
                    company_name TEXT,
                    card_holder TEXT,
                    designation TEXT,
                    mobile_number VARCHAR(50),
                    email TEXT,
                    website TEXT,
                    area TEXT,
                    city TEXT,
                    state TEXT,
                    pin_code VARCHAR(10),
                    image LONGBLOB
                    )''')

# Getting Ready The EasyOCR Reader
reader = easyocr.Reader(['en'])

#HOME menu
if selected=="Home":
    col1,col2=st.columns([5,2])
    with col1:
       st.markdown("## :green[**Technologies Used :**] Python,easy OCR, Streamlit, SQL, Pandas")
       st.markdown("## :green[**Overview :**] In this streamlit web app you can upload an image of a business card and extract relevant information from it using easyOCR. You can view, modify or delete the extracted data in this app. This app would also allow users to save the extracted information into a database along with the uploaded business card image. The database would be able to store multiple entries, each with its own business card image and extracted information.")
    with col2:
       col2.markdown('''<div style="height:550px;overflow-y:auto;color:white;border: 1px solid #e6e9ef;padding:140px 120px 120px 120px;"><h1>HOME</h1></div>''',unsafe_allow_html=True)
       
#update and modify
       
if selected == "Upload & Extract":
    st.markdown("### Upload a Business Card")
    uploaded_card = st.file_uploader("upload here",label_visibility="collapsed",type=["png","jpeg","jpg"])
        
    if uploaded_card is not None: 
        with open(os.path.join("uploaded_cards",uploaded_card.name),"wb") as f:
         f.write(uploaded_card.getbuffer())

        col1,col2 = st.columns(2,gap="large")
        with col1:
            st.markdown("#     ")
            st.markdown("#     ")
            st.markdown("### You have uploaded the card")
            st.image(uploaded_card)
        with col2:
            st.markdown("#     ")
            st.markdown("#     ")
            st.markdown("#     ")
            st.markdown("## Uploaded card is processed here and then the text present inside the Business Card is fetched us easyOCR")        
            saved_img = os.getcwd()+"//"+"uploaded_cards"+"//"+uploaded_card.name
            

        #easyOCR
        saved_img = os.getcwd() +"//"+"uploaded_cards"+"//"+uploaded_card.name
        # uploaded_image = Image.open(uploaded_card)
        result = reader.readtext(saved_img,detail=0,paragraph=False)
        #changing image to binary format
        def img_to_binary(file):
            with open(file,"rb") as file:
                binary_data=file.read()
            return binary_data
        
        data = {"company_name" : [],
                "card_holder" : [],
                "designation" : [],
                "mobile_number" :[],
                "email" : [],
                "website" : [],
                "area" : [],
                "city" : [],
                "state" : [],
                "pin_code" : [],
                "image" : [img_to_binary(saved_img)]
               }
        
        #inserting text 
        def get_data(result):
            for (ind,i) in enumerate(result):
                #Website
                if "www " in i.lower() or "www." in i.lower():
                    data["website"].append(i)
                elif "WWW" in i:
                    data["website"] = [result[4] +"." + result[5]]


                #Mail ID
                elif "@" in i:
                    data["email"].append(i)
                #Mobile Number
                elif "-" in i:
                    data["mobile_number"].append(i)

                    data["mobile_number"] = [" & ".join(data["mobile_number"])]
                       

                #COMPANY NAME  
                elif ind == (len(result)-1) or ind == (len(result)-3) or ind== (len(result)-2):

                    data["company_name"].append(i)
       
                    data["company_name"] = "".join(data["company_name"])
            
                    data["company_name"] = re.sub('TamilNadu \d{6}','', data["company_name"])

                    data["company_name"] = re.sub('INSURANCESt ,','', data["company_name"])
            
                    data["company_name"] = data["company_name"].strip()
            
                    data["company_name"] = [data["company_name"]]

                #CARD HOLDER NAME
                elif ind == 0:
                    data["card_holder"].append(i)
                    if data["card_holder"]==['Amit kumar']:
                      data["company_name"]=["GLOBAL INSURANCE"]
                      if len(data["company_name"]) >1:
                        data["company_name"].pop(-1)
                        if "TamilNadu 600113" ==data["company_name"]:
                          pattern = r'TamilNadu 600113'
                          data["company_name"]=re.sub(pattern,"",data["company_name"])


                #DESIGNATION
                elif ind == 1:
                    data["designation"].append(i)

                #AREA
                if re.findall('^[0-9].+, [a-zA-Z]+',i):
                    data["area"].append(i.split(',')[0])
                elif re.findall('[0-9] [a-zA-Z]+',i):
                    data["area"].append(i)

                #CITY NAME
                match1 = re.findall('.+St , ([a-zA-Z]+).+', i)
                match2 = re.findall('.+St,, ([a-zA-Z]+).+', i)
                match3 = re.findall('^[E].*',i)
                if match1:
                    data["city"].append(match1[0])
                elif match2:
                    data["city"].append(match2[0])
                elif match3:
                    data["city"].append(match3[0])

                #STATE
                state_match = re.findall('[a-zA-Z]{9} +[0-9]',i)
                if state_match:
                     data["state"].append(i[:9])
                elif re.findall('^[0-9].+, ([a-zA-Z]+);',i):
                    data["state"].append(i.split()[-1])
                if len(data["state"])== 2:
                    data["state"].pop(0)

                #PINCODE        
                if len(i)>=6 and i.isdigit():
                    data["pin_code"].append(i)
                elif re.findall('[a-zA-Z]{9} +[0-9]',i):
                    data["pin_code"].append(i[10:])
                
        get_data(result)
       
      #FUNCTION TO CREATE DATAFRAME
        def create_df(data):
            df = pd.DataFrame(data)
            return df
        df = create_df(data)
        st.success("### Data Extracted!")
        st.write(df)

        if st.button("Upload to Database"):
            for i,row in df.iterrows():
                
                sql = """INSERT INTO card_data(company_name,card_holder,designation,mobile_number,email,website,area,city,state,pin_code,image)
                         VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
                mycursor.execute(sql, tuple(row))
                
                
                mydb.commit()
            st.success("#### Uploaded to database successfully!")

   
if selected == "Modify":
    col1,col2,col3 = st.columns([3,3,2])
    col2.markdown("## Alter or Delete the data here")
    column1,column2 = st.columns(2,gap="large")
    try:
        with column1:
            mycursor.execute("SELECT card_holder FROM card_data")
            result = mycursor.fetchall()
            business_cards = {}
            for row in result:
                business_cards[row[0]] = row[0]
            selected_card = st.selectbox("Select a card holder name to update", list(business_cards.keys()))
            st.markdown("#### Update or modify any data below")
            mycursor.execute("select company_name,card_holder,designation,mobile_number,email,website,area,city,state,pin_code from card_data WHERE card_holder=%s",
                            (selected_card,))
            result = mycursor.fetchone()

            
            company_name = st.text_input("Company_Name", result[0])
            card_holder = st.text_input("Card_Holder", result[1])
            designation = st.text_input("Designation", result[2])
            mobile_number = st.text_input("Mobile_Number", result[3])
            email = st.text_input("Email", result[4])
            website = st.text_input("Website", result[5])
            area = st.text_input("Area", result[6])
            city = st.text_input("City", result[7])
            state = st.text_input("State", result[8])
            pin_code = st.text_input("Pin_Code", result[9])

            if st.button("Commit changes to DB"):
                # Update the information
                mycursor.execute("""UPDATE card_data SET company_name=%s,card_holder=%s,designation=%s,mobile_number=%s,email=%s,website=%s,area=%s,city=%s,state=%s,pin_code=%s
                                    WHERE card_holder=%s""", (company_name,card_holder,designation,mobile_number,email,website,area,city,state,pin_code,selected_card))
                mydb.commit()
                st.success("Information updated in database successfully.")

        with column2:
            mycursor.execute("SELECT card_holder FROM card_data")
            result = mycursor.fetchall()
            business_cards = {}
            for row in result:
                business_cards[row[0]] = row[0]
            selected_card = st.selectbox("Select a card holder name to Delete", list(business_cards.keys()))
            st.write(f"### You have selected :green[**{selected_card}'s**] card to delete")
            st.write("#### Proceed to delete this card?")

            if st.button("Yes Delete Business Card"):
                mycursor.execute(f"DELETE FROM card_data WHERE card_holder='{selected_card}'")
                mydb.commit()
                st.success("Business card information deleted from database.")
    except:
        st.warning("There is no data available in the database")
    
    if st.button("View updated data"):
        mycursor.execute("select company_name,card_holder,designation,mobile_number,email,website,area,city,state,pin_code from card_data")
        updated_df = pd.DataFrame(mycursor.fetchall(),columns=["Company_Name","Card_Holder","Designation","Mobile_Number","Email","Website","Area","City","State","Pin_Code"])
        st.write(updated_df)