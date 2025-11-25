import json
from typing import List, Dict, Union
from unstructured.partition.auto import partition
import fitz # PyMuPDF

def parse_document(file_path: str, file_type: str) -> str:
    """
    Parses various document types to extract text content.
    """
    elements = partition(filename=file_path)
    return "\n\n".join([str(el) for el in elements])

def parse_pdf(file_path: str) -> str:
    """
    Parses a PDF file to extract text content using PyMuPDF.
    """
    text_content = ""
    try:
        document = fitz.open(file_path)
        for page_num in range(document.page_count):
            page = document.load_page(page_num)
            text_content += page.get_text()
        document.close()
    except Exception as e:
        print(f"Error parsing PDF {file_path}: {e}")
        return ""
    return text_content

def parse_json(file_path: str) -> Union[Dict, List, None]:
    """
    Parses a JSON file.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error parsing JSON {file_path}: {e}")
        return None

def parse_html(file_path: str) -> str:
    """
    Reads the raw content of an HTML file.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error parsing HTML {file_path}: {e}")
        return ""
