import streamlit as st
import os
import json
from dotenv import load_dotenv
from parsers import parse_document, parse_pdf, parse_json, parse_html
from knowledge_base import KnowledgeBase
from test_case_agent import TestCaseAgent
from selenium_agent import SeleniumAgent

# Debugging line - should always show up
# st.write("Streamlit app is running!")

# Load environment variables
load_dotenv()

st.set_page_config(page_title="Autonomous QA Agent", layout="wide")
st.title("🧠 Autonomous QA Agent")


# Initialize session state variables if they don't exist
if 'kb' not in st.session_state:
    st.session_state.kb = None
if 'test_cases' not in st.session_state:
    st.session_state.test_cases = []

# Phase 1: Knowledge Base Ingestion & UI
st.header("Phase 1: Knowledge Base Ingestion")

with st.expander("Upload Documents and Build Knowledge Base"):
    st.subheader("Upload Support Documents")
    support_docs = st.file_uploader(
        "Upload your product specifications, UI/UX guidelines, etc. (MD, TXT, JSON, PDF)",
        type=["md", "txt", "json", "pdf"],
        accept_multiple_files=True
    )

    st.subheader("Upload Target Web Project (checkout.html)")
    checkout_html = st.file_uploader(
        "Upload the checkout.html file",
        type=["html"],
        accept_multiple_files=False
    )

    if st.button("Build Knowledge Base"):
        if not support_docs and not checkout_html:
            st.warning("Please upload at least one document or the checkout.html file.")
        else:
            st.info("Building Knowledge Base...")
            
            kb = KnowledgeBase()
            
            # Create a temporary directory for uploaded files
            temp_dir = "./temp_docs"
            os.makedirs(temp_dir, exist_ok=True)

            # Process support documents
            for doc_file in support_docs:
                file_path = os.path.join(temp_dir, doc_file.name)
                with open(file_path, "wb") as f:
                    f.write(doc_file.getbuffer())
                
                content = ""
                if doc_file.type == "application/pdf":
                    content = parse_pdf(file_path)
                elif doc_file.type == "application/json":
                    json_data = parse_json(file_path)
                    content = json.dumps(json_data, indent=2) if json_data else ""
                else: # md, txt
                    content = parse_document(file_path, doc_file.type)
                
                if content:
                    kb.add_documents([content], [{"source_document": doc_file.name}])
                os.remove(file_path) # Clean up temp file

            # Process checkout.html
            if checkout_html:
                file_path = os.path.join(temp_dir, checkout_html.name)
                with open(file_path, "wb") as f:
                    f.write(checkout_html.getbuffer())
                
                html_content = parse_html(file_path)
                if html_content:
                    kb.add_documents([html_content], [{"source_document": checkout_html.name, "type": "html"}])
                os.remove(file_path) # Clean up temp file
            
            # # Clean up the temporary directory if it's empty - Removed for debugging
            # if not os.listdir(temp_dir):
            #     os.rmdir(temp_dir)

            st.session_state.kb = kb # Store KnowledgeBase in session state
            st.success("Knowledge Base Built!")

# Phase 2: Test Case Generation Agent
st.header("Phase 2: Test Case Generation Agent")

# Get API key from environment
gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    st.error("Gemini API key not found. Please set it in a .env file (e.g., GEMINI_API_KEY='YOUR_API_KEY').")

with st.expander("Generate Test Cases"):
    if st.session_state.kb is None:
        st.warning("Please build the Knowledge Base first in Phase 1.")
    elif not gemini_api_key:
        st.warning("Gemini API key is missing. Please set it in the .env file.")
    else:    
        user_query = st.text_input(
            "Enter your query for test case generation.",
            value="Generate all positive and negative test cases for the discount code feature."
        )
        if st.button("Generate Test Cases"):
            if not user_query:
                st.warning("Please enter a query to generate test cases.")
            else:
                st.info("Generating Test Cases...")
                test_case_agent = TestCaseAgent(st.session_state.kb, gemini_api_key)
                test_cases_result = test_case_agent.generate_test_cases(user_query)
                
                if isinstance(test_cases_result, dict) and "error" in test_cases_result:
                    st.error(test_cases_result["error"])
                    st.session_state.test_cases = [] # Clear test cases on error
                elif isinstance(test_cases_result, list):
                    st.session_state.test_cases = test_cases_result # Store generated test cases
                    st.json(test_cases_result)
                    st.success("Test Cases Generated!")
                else:
                    st.error("Unexpected format for generated test cases.")
                    st.session_state.test_cases = []

# Phase 3: Selenium Script Generation Agent
st.header("Phase 3: Selenium Script Generation Agent")

with st.expander("Generate Selenium Test Script"):
    if st.session_state.kb is None or not st.session_state.test_cases:
        st.warning("Please build the Knowledge Base and generate Test Cases first.")
    elif not gemini_api_key:
        st.warning("Gemini API key is missing. Please set it in the .env file.")
    else:
        test_case_options = [
            f"{tc.get('Test_ID', 'N/A')}: {tc.get('Test_Scenario', 'N/A')}"
            for tc in st.session_state.test_cases
        ]
        selected_test_case_description = st.selectbox(
            "Select Test Case",
            test_case_options,
            index=0
        )

        if st.button("Generate Selenium Script"):
            if not selected_test_case_description:
                st.warning("Please select a test case first.")
            else:
                st.info(f"Generating Selenium script for: {selected_test_case_description}...")
                
                # Find the actual test case object
                selected_test_case = next(
                    (tc for tc in st.session_state.test_cases 
                     if f"{tc.get('Test_ID', 'N/A')}: {tc.get('Test_Scenario', 'N/A')}" == selected_test_case_description),
                    None
                )

                if selected_test_case:
                    selenium_agent = SeleniumAgent(st.session_state.kb, gemini_api_key)
                    selenium_script = selenium_agent.generate_selenium_script(selected_test_case)

                    if isinstance(selenium_script, dict) and "error" in selenium_script:
                        st.error(selenium_script["error"])
                    else:
                        st.code(selenium_script, language="python")
                        st.success("Selenium Script Generated!")
                else:
                    st.error("Selected test case not found.")
