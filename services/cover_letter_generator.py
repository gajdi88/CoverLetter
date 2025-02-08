# services/cover_letter_generator.py

import requests
from dotenv import load_dotenv
from pdfminer.high_level import extract_text
import re
import pdfplumber
import os
import os
from docx import Document

load_dotenv()


def clean_prompt(prompt: str) -> str:
    """
    Cleans the input prompt by removing special characters that might cause issues in JSON or API requests.

    This function:
      - Replaces newline characters with spaces.
      - Removes characters that are not alphanumeric, whitespace, or one of: . , : ; ? ! ' " -
      - Collapses multiple spaces into a single space.

    Args:
        prompt (str): The original prompt containing special characters.

    Returns:
        str: A cleaned version of the prompt.
    """
    # Replace newline characters with a space
    # prompt = prompt.replace('\n', ' ')

    # Remove any characters that are not allowed.
    # Allowed: letters, digits, whitespace, and basic punctuation (. , : ; ? ! ' " -)
    cleaned = re.sub(r'[^A-Za-z0-9\s\.\,\:\;\?\'\!\-]', '', prompt)

    # Collapse multiple spaces into a single space and trim leading/trailing whitespace
    cleaned = re.sub(r'[ \t\r\f+]', ' ', cleaned).strip()
    # cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

class CoverLetterGenerator:
    def __init__(self):
        self.conversation_history = []
        api_key = os.environ.get("API_KEY")
        self.headers = {"Authorization": f"Bearer {api_key}"}
        print(self.headers)

    def extract_text(self, cv_path):
        """
        Extract text from CV file.
        Implement actual extraction logic here.
        """
        # Extract raw text from the PDF file
        # raw_text = extract_text(cv_path)

        # with pdfplumber.open(cv_path) as pdf:
        #     raw_text = ''
        #     for page in pdf.pages:
        #         raw_text += page.extract_text()

        doc = Document(cv_path)
        raw_text = []
        for para in doc.paragraphs:
            raw_text.append(para.text)
        return '\n'.join(raw_text)

        return raw_text

    def generate_cover_letter(self, cv_path, job_description):
        """
        Generate cover letter using Ollama via OpenWebUI.

        Args:
            cv_path (str): Path to the CV file.
            job_description (str): Job description provided by the user.

        Returns:
            str: Generated cover letter text or error message if fails.
        """

        try:
            # Extract text from CV
            cv_text = self.extract_text(cv_path)

            # Create prompt for generating cover letter
            prompt = f"""
                Write a cover letter based on this CV:
                --------
                {cv_text}
                ---------
                and the following job description:
                ---------
                {job_description}
            """
            cleaned_prompt = clean_prompt(prompt)

            print(cleaned_prompt)

            # Append current prompt to conversation history
            self.conversation_history.append(cleaned_prompt)

            # Prepare messages for Ollama API request
            messages = [{"role": "user", "content": msg} for msg in self.conversation_history]

            api_message = f"""
                {{
                  "model": "deepseek-r1:32b",
                  "prompt": "{cleaned_prompt}",
                  "stream": false
                }}
                """

            response = ""
            # Send request to Ollama API
            response = requests.post(
                'http://localhost:3000/ollama/api/generate',
                data=api_message,
                headers=self.headers
            )
            response.raise_for_status()

            # Extract the generated text from Ollama's response
            generated_text = response.json()['response']

            # Append the generated text to conversation history for future context
            self.conversation_history.append(generated_text)

            return generated_text

        except requests.exceptions.RequestException as e:
            print(f"Error communicating with Ollama API: {e}")
            return "Unable to generate cover letter at this time."

    def reset_history(self):
        """
        Reset the conversation history for a new session.
        """
        self.conversation_history = []