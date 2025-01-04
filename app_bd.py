import streamlit as st
import pandas as pd
from streamlit_cognito_auth import CognitoAuthenticator
import os
from PyPDF2 import PdfReader
import json
import boto3
from anthropic import Anthropic


pool_id = "us-west-2_WIk3nH6HJ"
app_client_id = "1t6aft7haelaqg723mtruhan3s"


# anthropic 
anthropic = Anthropic(
    api_key="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"
)
anthropic_model_id = "claude-3-5-sonnet-latest"
 
# Authenticate user
if pool_id and app_client_id:
    authenticator = CognitoAuthenticator(
        pool_id=pool_id,
        app_client_id=app_client_id,
    )
    #authenticator.logout()
    is_logged_in = authenticator.login()
    st.session_state['is_logged_in'] = is_logged_in
    if not is_logged_in:
        st.stop()
    
def extract_text_from_pdf(pdf_file):
    pdf_reader = PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def call_anthopric(model_id, messages): 
    response = anthropic.messages.create(
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": messages,
            }
        ],
        model=model_id,
    )
    return response

if __name__ == "__main__":

    st.title("Path Planer")
    st.write("Welcome to PathPlanner, your personal academic advisor for achieving your goals! Follow these simple steps to get started:")

    
    goal = st.pills(
        "Your goal",
        default="Go to college",
        options=("Get a high school diploma", "Go to college"),
    )

    grade_level = st.pills(
        "Your upcoming high school year",
        default="Grade 9",
        options=("Grade 9", "Grade 10"),
    )

    # select interested majors
    # Load the CSV data

    df = pd.read_csv("data/data.csv")

    # Remove NaN values from the 'Major' column
    df_cleaned = df["Major"].dropna()

    # Add 'None' as the first option (if desired)
    majors = ["None"] + df_cleaned.tolist()

    # Initialize the multiselect widget
    # Default value will only be "None" if the user hasn't selected anything yet
    majors_selected = st.multiselect(
    "Choose 2 of your interested majors", 
    options=majors,  # List of options including "None"
    default=[] if len(df_cleaned) > 1 else ["None"],  # Default to "None" if no major is selected
    max_selections=2  # Limiting to 2 selections
    )

    # 1. Subjects they excel in and those they struggle with (Text Area)
    subjects_excel = st.text_area(
    "What subjects do you excel in? Please list them:",
    placeholder="List subjects you excel in here."
    )

    subjects_struggle = st.text_area(
    "Do you struggle with any subjects? Please list them:",
    placeholder="List subjects you struggle with here."
    )

    # 2. Interest in taking advanced courses (AP, honors, IB, etc.) - Multiselect remains
    advanced_courses = st.multiselect(
    "Are you interested in taking any advanced courses? Choose all that applies", 
    options=["AP", "Honors", "IB", "Other Acceleration Options"],
    default=[]
    )

    # 3. Special circumstances (learning differences, work commitments, etc.)
    special_circumstances = st.text_area(
    "Do you have any special circumstances (learning differences, work commitments, family obligations, etc.) that should be considered when generating your course plan?",
    placeholder="Please describe any special circumstances here."
    )

    # 4. Specific subjects or extracurricular activities they are passionate about (Text Area)
    passionate_about = st.text_area(
    "What subjects or extracurricular activities are you passionate about and would like to explore further?", 
    placeholder="Describe subjects or activities you're passionate about."
    )

    # Ask if the student has already taken some classes
    classes_taken = st.text_area("Have you already taken any high school classes? Please list them: (Write 'None' if not applicable.)")


    #majors = st.multiselect("choose 2 of your interested majors", options=df.columns[1:], default=["None"], max_selections=2)
    #score_sat = st.number_input("Your recent SAT score", placeholder=1200, step=100, min_value=400, max_value=1500)
    #st.write("or")
    
    score_gpa = st.number_input("What is your Target Weighted GPA score?", placeholder=4.0, step=0.1, min_value=2.5, max_value=5.0)

    uploaded_file = st.file_uploader("Upload the school course catalog document", type="pdf")
    pdf_text = None

    if uploaded_file is not None:
        try:
            # Extract text
            pdf_text = extract_text_from_pdf(uploaded_file)
        except Exception as e:
            st.error(f"An error occurred while processing the PDF: {e}")

        if st.button("Get recommendation"):
            # Send to LLM

            anthropic_prompts = f'''
                                You are a school advisor assisting high school students in creating a 3-4 year course plan to achieve their goals. generate the plan of specific courses in a table format
                                The student will provide the following information to help construct a 3-4 year course plan:
                                My goal is {goal}
                                My upcoming grade level is {grade_level}
                                The majors I am most interested in are {majors_selected}
                                The school course catalog: {pdf_text}
                                The highschool classes that I have already taken, and thus don't include in my plan are:{classes_taken}
                                The subjects I excel in and would love to take in my course plan are:{subjects_excel}
                                The subjects I struggle in and would like to take the regular version(for required courses) and not take if it's not required are:{subjects_struggle}
                                Their current grade level.
                                The types of advanced courses that I am intersted in are:{advanced_courses}
                                I have some special circumstances that might impact my course plan:{special_circumstances}
                                Some subjects and extracurriculars that I am passionate about include:{passionate_about}
                                
                                Based on this information, please create a comprehensive, balanced course plan that aligns with the student’s academic and career aspirations, supports their strengths and weaknesses, and incorporates their interests and extracurricular goals.
                                Finally, calculate a estimated GPA, asssuming that the student averages an A across 4 years. Keep in mind that accelerated courses such as honors, APs, and IB's grant a 5 instead of a 4 for As.
            '''
            # call bedrock
            with st.spinner('Evaluating...'):
                #response = call_bedrock(bedrock_model_id, messages)
                response = call_anthopric(anthropic_model_id,anthropic_prompts)
                
                st.write(response.content[0].text)