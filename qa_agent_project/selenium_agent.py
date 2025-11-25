import os
import json
from typing import Dict, Union, List
from knowledge_base import KnowledgeBase
import google.generativeai as genai

class SeleniumAgent:
    def __init__(self, knowledge_base: KnowledgeBase, api_key: str, llm_model: str = "gemini-2.5-flash"):
        self.knowledge_base = knowledge_base
        genai.configure(api_key=api_key)
        self.llm = genai.GenerativeModel(llm_model)

    def generate_selenium_script(self, test_case: Dict) -> Union[str, Dict]:
        """
        Generates a runnable Selenium Python script for a given test case.
        """
        test_id = test_case.get("Test_ID", "N/A")
        feature = test_case.get("Feature", "N/A")
        test_scenario = test_case.get("Test_Scenario", "N/A")
        expected_result = test_case.get("Expected_Result", "N/A")
        grounded_in = test_case.get("Grounded_In", "N/A")

        # Retrieve the full content of checkout.html
        html_docs, html_metadatas = self.knowledge_base.query(
            "checkout.html content", 
            n_results=10, # Retrieve more chunks to ensure full HTML is captured
            where={"type": "html"}
        )
        full_html_content = "\n".join(html_docs) if html_docs else "No checkout.html content found."
        
        # Retrieve relevant documentation snippets from the vector DB for the feature
        relevant_docs, relevant_metadatas = self.knowledge_base.query(
            f"Documentation for {feature} related to {test_scenario}",
            n_results=5,
            where={"type": {"!=": "html"}} # Exclude HTML content here, already retrieved
        )
        documentation_context = "\n\n".join(relevant_docs) if relevant_docs else "No specific documentation context found."

        prompt = f"""
        You are an expert Selenium (Python) test engineer. Your task is to generate a fully executable
        Python Selenium script to automate the given test case on the provided HTML structure.

        Follow these instructions carefully:
        1.  **Use appropriate selectors**: Identify elements using their IDs, names, CSS selectors, or XPath based on the provided HTML. Prioritize IDs where available.
        2.  **Chrome WebDriver**: Assume Chrome is installed and use `webdriver.Chrome()`.
        3.  **Local HTML File**: The script should open the `checkout.html` file directly using its local path. Provide a placeholder path like `file:///C:/path/to/checkout.html` and mention in comments that the user needs to update it.
        4.  **Action Steps**: Translate the `Test_Scenario` into concrete Selenium actions (e.g., `send_keys`, `click`).
        5.  **Assertions**: Implement assertions to verify the `Expected_Result`. Use `assert` statements. If a visual change is expected (e.g., red text), explain how Selenium would verify this (e.g., checking CSS properties or element text).
        6.  **Setup and Teardown**: Include `driver.quit()` at the end of the test function.
        7.  **Docstrings and Comments**: Add comments where necessary to explain complex logic or placeholders.
        8.  **Output**: Provide only the Python code block, no extra conversational text.

        ---
        Test Case Details:
        Test ID: {test_id}
        Feature: {feature}
        Test Scenario: {test_scenario}
        Expected Result: {expected_result}
        Grounded In: {grounded_in}

        ---
        Full `checkout.html` content:
        ```html
        {full_html_content}
        ```

        ---
        Relevant Documentation Snippets:
        ```
        {documentation_context}
        ```

        Generate the Python Selenium script:
        ```python
        # Your Python Selenium script here
        ```
        """

        try:
            response = self.llm.generate_content(prompt)
            llm_output = response.text
            
            # Extract only the code block
            if "```python" in llm_output and "```" in llm_output:
                start = llm_output.find("```python") + len("```python")
                end = llm_output.find("```", start)
                if start != -1 and end != -1:
                    return llm_output[start:end].strip()
            return llm_output # Fallback if code block not found
        except Exception as e:
            return {"error": f"Failed to generate Selenium script with Gemini API: {e}. Ensure your API key is correct and you have access to the '{self.llm_model}' model."}
