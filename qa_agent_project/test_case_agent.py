import os
import json
from typing import List, Dict, Union, Tuple
from knowledge_base import KnowledgeBase
import google.generativeai as genai

class TestCaseAgent:
    def __init__(self, knowledge_base: KnowledgeBase, api_key: str, llm_model: str = "gemini-2.5-flash"):
        self.knowledge_base = knowledge_base
        genai.configure(api_key=api_key)
        self.llm = genai.GenerativeModel(llm_model)

    def generate_test_cases(self, user_query: str) -> Union[str, Dict]:
        """
        Generates test cases based on user query and retrieved context using an LLM.
        """
        # 1. Embed the user's query and retrieve relevant chunks
        retrieved_documents, retrieved_metadatas = self.knowledge_base.query(user_query, n_results=7)

        context_str = "\n\n".join([doc for doc in retrieved_documents])
        source_documents = ", ".join(list(set([meta['source_document'] for meta in retrieved_metadatas])))

        # 2. Construct the prompt for the LLM
        prompt = f"""
        You are an intelligent QA agent tasked with generating comprehensive test cases.
        Your goal is to produce structured test plans in JSON format based on the user's query and the provided context.
        Each test case must include:
        - Test_ID: A unique identifier (e.g., TC-001)
        - Feature: The feature being tested
        - Test_Scenario: A clear description of the test scenario
        - Expected_Result: The expected outcome of the test
        - Grounded_In: The source document(s) from which the information was derived.

        Ensure that all test reasoning and expected results are strictly grounded in the provided documentation.
        If the context is insufficient to generate a specific test case, state that.

        User Query: "{user_query}"

        Context from Knowledge Base (Documentation and HTML):
        ---
        {context_str}
        ---

        Based on the User Query and the provided Context, generate the test cases in a JSON array format.
        Example format:
        [
            {{
                "Test_ID": "TC-001",
                "Feature": "Discount Code",
                "Test_Scenario": "Apply a valid discount code 'SAVE15'.",
                "Expected_Result": "Total price is reduced by 15%.",
                "Grounded_In": "product_specs.md"
            }},
            {{
                "Test_ID": "TC-002",
                "Feature": "User Details Form",
                "Test_Scenario": "Submit form with invalid email format.",
                "Expected_Result": "An inline error message 'Invalid email format' is displayed in red text next to the email field.",
                "Grounded_In": "ui_ux_guide.txt"
            }}
        ]
        """

        # 3. Feed retrieved context + user query into an LLM (Gemini API)
        try:
            response = self.llm.generate_content(prompt)
            llm_output = response.text
            
            # Extract JSON from markdown code block if present
            if llm_output.strip().startswith("```json") and llm_output.strip().endswith("```"):
                llm_output = llm_output.strip()[len("```json"):-len("```")].strip()

            # Attempt to parse as JSON, otherwise return an error dictionary
            try:
                parsed_output = json.loads(llm_output)
                if isinstance(parsed_output, list): # Ensure the output is a list of test cases
                    return parsed_output
                else:
                    print("Warning: LLM output was valid JSON but not a list. Returning error.")
                    return {"error": "LLM output was valid JSON but not a list of test cases."}
            except json.JSONDecodeError:
                print("Warning: LLM output was not valid JSON. Returning error.")
                return {"error": "LLM output was not valid JSON. Please refine your query or context."}
        except Exception as e:
            return {"error": f"Failed to generate test cases with Gemini API: {e}. Ensure your API key is correct and you have access to the '{self.llm_model}' model."}
