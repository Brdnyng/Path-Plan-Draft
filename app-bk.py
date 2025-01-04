import streamlit as st
from streamlit_cognito_auth import CognitoAuthenticator
import os
from PyPDF2 import PdfReader
import json
import boto3
from openai import OpenAI


pool_id = "us-west-2_WIk3nH6HJ" 
app_client_id = "1t6aft7haelaqg723mtruhan3s"

# AWS Bedrock LLMs settings
#aws_key = st.secrets.get("AWS_KEY")
#aws_secret = st.secrets.get("AWS_SECRET")
#aws_region = 'us-west-2'
bedrock_model_id = "anthropic.claude-3-5-sonnet-20240620-v1:0"

# OpenAI LLMs settings
#openai_key = "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"
#openai_model_id = "gpt-4o-mini"
 

 
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

def call_bedrock(model_id,
                          msgs):
    bedrock_runtime = boto3.client('bedrock-runtime',
                                aws_access_key_id=aws_key,
                                aws_secret_access_key=aws_secret,
                                region_name=aws_region)

    system_prompts, contents = [], []
    for m in msgs:
        print(m)
        if m["role"] == "system":
            system_prompts.append({"text": m["text"]})
        elif m["role"] == "user":
            contents.append({
                "text": m["text"]
            })
    messages=[
                {"role": "user", "content": contents},
            ]

    # Inference parameters to use.
    temperature = 0.5
    top_k = 200

    # Base inference parameters to use.
    inference_config = {"temperature": temperature}
    # Additional inference parameters to use.
    additional_model_fields = {"top_k": top_k}

    # Send the message.
    response = bedrock_runtime.converse(
        modelId=model_id,
        messages=messages,
        system=system_prompts,
        inferenceConfig=inference_config,
        additionalModelRequestFields=additional_model_fields
    )

    if response:
        return response.get("output",{}).get("message",{}).get("content",[{}])[0].get("text")
    return None

def call_openai(openai_model_id, messages):
    openai = OpenAI(api_key=openai_key)
    chat_completion = openai.chat.completions.create(
        messages=messages,
        model=openai_model_id,
    )
    print(chat_completion)
    return chat_completion

if __name__ == "__main__":

    st.title("Path Planer")
    st.write("Welcome to PathPlanner, your personal academic advisor for achieving your goals! Follow these simple steps to get started:")

    goal = st.pills(
        "Your goal",
        default="Go to college",
        options=("Get a high school diploma", "Go to college"),
    )

    grade_level = st.pills(
        "Your current high school year",
        default="Grade 9",
        options=("Grade 9", "Grade 10"),
    )

    score_sat = st.number_input("Your recent SAT score", placeholder=1200, step=100, min_value=400, max_value=1500)
    st.write("or")
    score_gpa = st.selectbox("Your recent GPA score", [0,1,2,3,4,5])

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
            messages = [{
                            "role": "system",
                            "text": """
                                You are a school advisor assisting high school students in creating a plan to achieve their goals. 
                                The student will share their objective—either graduating with a diploma or pursuing college admission, along with their current grade level, most recent standardized test scores or GPA, and a course catalog document provided by their high school. Based on this information, provide three tailored options categorized as:
                                Safety: A plan that aligns with easily attainable requirements.
                                Target: A plan that is realistic but requires consistent effort to achieve.
                                Reach: An ambitious plan requiring significant improvement or exceptional performance.
                                Include the required GPA and any additional recommendations for each option.
                                """
                        },
                        {
                            "role": "user",
                            "text": f"My goal is {goal}",
                        },
                        {
                            "role": "user",
                            "text": f"My current grade level is {grade_level}"
                        },
                        {
                            "role": "user",
                            "text": f"My recent SAT is {score_sat}"
                        },
                        {
                            "role": "user",
                            "text": f"The school course catalog: {pdf_text}"
                        }
                    ]

            # call bedrock
            with st.spinner('Evaluating...'):
                response = call_openai(openai_model_id, messages)
                #response = call_bedrock(bedrock_model_id, messages)
                
                st.write(response)


