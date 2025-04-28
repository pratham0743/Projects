import streamlit as st
import numpy as np
import pandas as pd
import sqlite3 
import hashlib
import os
import csv
import utils
import spacy
import pprint
from spacy.matcher import Matcher
import multiprocessing as mp
import streamlit as st
from fpdf import FPDF
import nltk

conn = sqlite3.connect('data.db')
c = conn.cursor()
csv_file_path = 'skills.csv'

with open(csv_file_path, 'r') as file:
    reader = csv.reader(file)
    data_list = [item for row in reader for item in row]

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Resume', 0, 1, 'C')

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(5)

    def chapter_body(self, body):
        self.set_font('Arial', '', 12)
        self.multi_cell(0, 10, body)
        self.ln()

class ResumeParser(object):
    def __init__(self, resume):
        nlp = spacy.load('en_core_web_sm')
        self.__matcher = Matcher(nlp.vocab)
        self.__details = {
            'name'              : None,
            'email'             : None,
            'mobile_number'     : None,
            'skills'            : None,
            'projects'          : None
        }
        self.__resume      = resume
        self.__text_raw    = utils.extract_text(self.__resume, os.path.splitext(self.__resume)[1])
        self.__text        = ' '.join(self.__text_raw.split())
        self.__nlp         = nlp(self.__text)
        self.__noun_chunks = list(self.__nlp.noun_chunks)
        self.__get_basic_details()

    def get_extracted_data(self):
        return self.__details

    def __get_basic_details(self):
        name       = utils.extract_name(self.__nlp, matcher=self.__matcher)
        email      = utils.extract_email(self.__text)
        mobile     = utils.extract_mobile_number(self.__text)
        skills     = utils.extract_skills(self.__nlp, self.__noun_chunks)
        entities   = utils.extract_entity_sections(self.__text_raw)
        experience = utils.extract_experience(self.__text)
        # projects = utils.extract_projects(self.__nlp, matcher=self.__matcher)
        self.__details['name'] = name
        self.__details['email'] = email
        self.__details['mobile_number'] = mobile
        self.__details['skills'] = skills
        self.__details['experience'] = experience
        # self.__details['projects'] = projects

        return

def resume_result_wrapper(resume):
        parser = ResumeParser(resume)
        return parser.get_extracted_data()
    

def upload_and_store_files(uploaded_files):
    resume_folder = "resumes"
    os.makedirs(resume_folder, exist_ok=True)

    for file in uploaded_files:
        file_extension = file.name.split(".")[-1].lower()
        if file_extension in ["docx", "pdf"]:
            file_path = os.path.join(resume_folder, file.name)
            with open(file_path, "wb") as f:
                f.write(file.getbuffer())
    st.success("Files are successfully uploaded and stored.")

def upload_and_store_files2(uploaded_files):
    resume_folder = "shared_resumes"
    os.makedirs(resume_folder, exist_ok=True)

    for file in uploaded_files:
        file_extension = file.name.split(".")[-1].lower()
        if file_extension in ["docx", "pdf"]:
            file_path = os.path.join(resume_folder, file.name)
            with open(file_path, "wb") as f:
                f.write(file.getbuffer())
    st.success("Files are successfully uploaded and stored.")

def delete_files_in_resumes_directory():
    for root, directories, filenames in os.walk('resumes'):
        for filename in filenames:
            file_path = os.path.join(root, filename)
            try:
                os.remove(file_path)
                print(f"File '{filename}' deleted successfully.")
            except Exception as e:
                print(f"Error deleting file '{filename}': {e}")  


def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()


def check_hashes(password,hashed_text):
    if make_hashes(password) == hashed_text:
        return hashed_text
    return False


def create_usertable():
    c.execute('CREATE TABLE IF NOT EXISTS userstable(username TEXT,password TEXT, user_type TEXT)')


def add_userdata(username,password, user_type):
    c.execute('INSERT INTO userstable(username,password, user_type) VALUES (?,?,?)',(username,password, user_type))
    conn.commit()

def login_user(username,password, user_type):
    c.execute('SELECT * FROM userstable WHERE username =? AND password = ? AND user_type = ?',(username,password, user_type))
    data = c.fetchall()
    return data


def view_all_users():
    c.execute('SELECT * FROM userstable')
    data = c.fetchall()
    return data


def main():
    pool = mp.Pool(mp.cpu_count())
    resumes = []
    data = []
    st.subheader('Resume Parsing Using Name Entity Recognition')
    st.sidebar.subheader("MET's Institute Of Engineering, Nashik, Maharashtra, India")
    st.sidebar.subheader("Information Technology Department")
    menu = ["Home","Login","SignUp"]
    choice = st.sidebar.selectbox("Menu",menu)

    if choice == "Home":
        # st.markdown('<div style="text-align: justify;">Resume parsing using Named Entity Recognition (NER) is a sophisticated technique employed in natural language processing to automatically extract relevant information from resumes. NER involves training machine learning models to identify and classify entities within text, such as names, organizations, locations, dates, and more. In the context of resume parsing, NER algorithms are trained specifically to recognize entities like candidate names, educational institutions, job titles, skills, certifications, and work experience. When a resume is fed into the system, the NER model analyzes the text and identifies these entities, extracting structured data that can then be used for various purposes such as talent acquisition, candidate screening, or skills matching. </div>', unsafe_allow_html=True)
        st.image("poster.png")
        # st.markdown('<div style="text-align: justify;">One of the key advantages of resume parsing with NER is its ability to accurately and efficiently extract relevant information from resumes, saving significant time and effort in manual data entry and analysis. By automating the extraction process, organizations can streamline their recruitment workflows, quickly identify qualified candidates, and make data-driven decisions. Additionally, NER models can be continuously trained and refined to improve accuracy and adapt to evolving resume formats and language variations, ensuring reliable performance across diverse datasets. Overall, resume parsing using NER represents a powerful tool for modern HR and recruitment processes, enhancing efficiency, scalability, and the overall candidate experience.</div>', unsafe_allow_html=True)






    elif choice == "Login":
        user_type = st.sidebar.selectbox("User Type",['Admin(HR)','User'])
        username = st.sidebar.text_input("User Name")
        password = st.sidebar.text_input("Password",type='password')
        if st.sidebar.checkbox("Login/Logout"):
            create_usertable()
            hashed_pswd = make_hashes(password)
            result = login_user(username,check_hashes(password,hashed_pswd), user_type)
            if result:
                st.sidebar.success("Login Success")
                if(user_type == 'Admin(HR)'):
                    menu = ["Resume Parsing","Resume Generation"]
                else:
                    menu = ["Resume Generation", "Resume Upload"]
                choice = st.selectbox("Menu",menu)
                if choice == "Resume Parsing":

                    st.subheader("Upload Resume for Parsing ")
                    uploaded_files = st.file_uploader("Choose .docx or .pdf files", type=["docx", "pdf"], accept_multiple_files=True)
                    if uploaded_files:
                        upload_and_store_files(uploaded_files)
                            
                        for root, directories, filenames in os.walk('resumes'):
                            for filename in filenames:
                                file = os.path.join(root, filename)
                                resumes.append(file)
                        results = [pool.apply_async(resume_result_wrapper, args=(x,)) for x in resumes]
                        results = [p.get() for p in results]
                        df = pd.DataFrame(results)
                        df['skills'] = df['skills'].apply(lambda x: ', '.join(x).split(','))
                        df['skills'].drop_duplicates()
                        st.write(df)
                        delete_files_in_resumes_directory()
                        selected_skill = st.text_input('Enter Skill to Filter:')
                        if selected_skill:
                            filtered_df = df[df['skills'].apply(lambda x: any(selected_skill.lower() in skill.lower() for skill in x))]
                            if filtered_df.empty:
                                st.warning("No Resume found with matching Skills.")
                            else:
                                st.write(filtered_df)
                elif choice == "Resume Upload":
                    st.subheader("Upload Resume to send HR")
                    uploaded_files = st.file_uploader("Choose .docx or .pdf files", type=["docx", "pdf"], accept_multiple_files=True)
                    if uploaded_files:
                        upload_and_store_files2(uploaded_files)
                        
                elif choice == "Resume Generation":
                    st.subheader("Resume Generation")
                    with st.form("resume_form"):
                        st.write("## Create Your Resume")
                        fullname = st.text_input("Full Name")
                        email = st.text_input("Email Address")
                        contact = st.text_input("Contact Number")
                        career_obj = st.text_area("Career Objective")
                        education = st.text_area("Educational Qualification")
                        skills = st.text_area("Skills (separate with commas)")
                        experience = st.text_area("Experience")
                        projects = st.text_area("Projects")
                        certification = st.text_area("Certification")
                        # certificate = st.file_uploader("Upload Certificate (PDF)", type="pdf")
                        submit_button = st.form_submit_button("Generate Resume")

                    if submit_button:
                        pdf = PDF()
                        pdf.add_page()

                        pdf.set_font('Arial', 'B', 16)
                        pdf.cell(0, 10, fullname, 0, 1, 'C')
                        pdf.set_font('Arial', '', 12)
                        pdf.cell(0, 10, email, 0, 1, 'C')
                        pdf.cell(0, 10, contact, 0, 1, 'C')
                        pdf.ln(10)

                        pdf.chapter_title('Career Objective')
                        pdf.chapter_body(career_obj)

                        pdf.chapter_title('Educational Qualification')
                        pdf.chapter_body(education)

                        pdf.chapter_title('Skills')
                        pdf.chapter_body(skills)

                        pdf.chapter_title('Experience')
                        pdf.chapter_body(experience)

                        pdf.chapter_title('Projects')
                        pdf.chapter_body(projects)

                        pdf.output('Resume.pdf')

                        with open('Resume.pdf', 'rb') as file:
                            st.download_button(label="Download Resume",
                                               data=file,
                                               file_name="Resume.pdf",
                                               mime="application/pdf")
            else:
                    st.sidebar.warning("Incorrect Username/Password")
        else:
                st.sidebar.warning("Please Enter Valid Credentials...")
    elif choice == "SignUp":
        st.subheader("Create New Account")
        user_type = st.selectbox("User Type",['Admin(HR)','User'])
        new_user = st.text_input("Username")
        new_password = st.text_input("Password",type='password')
        if st.button("Signup"):
            if(new_user!='' and new_password!=''):
                create_usertable()
                add_userdata(new_user,make_hashes(new_password), user_type)
                st.success("You have successfully created a valid Account")
                st.info("Go to Login Menu to login")
            else:
                st.warning("Please Enter Valid Credentials...")
if __name__ == "__main__":
    main()
