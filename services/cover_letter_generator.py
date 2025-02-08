# services/cover_letter_generator.py

import requests
from dotenv import load_dotenv
import re
import pdfplumber
import os
import os
import json
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
    # cleaned = re.sub(r'[^A-Za-z0-9\s\.\,\:\;\?\'\!\-]', '', prompt)
    cleaned = re.sub(r'[^A-Za-z0-9\s\.\,\:\;\?\'\"\!\-]', '', prompt)

    # Collapse multiple spaces into a single space and trim leading/trailing whitespace
    cleaned = re.sub(r'[ \t\r\f+]', ' ', cleaned).strip()

    # Optionally remove extra spaces after newline
    cleaned = re.sub(r'\n\s+', '\n', cleaned).strip()

    # completely remove new lines
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

    def query_llm(self, prompt, model_choice="deepseek-r1:32b"):

        response = ""

        # Build your payload as a Python dictionary
        payload = {
            "model": model_choice,
            "prompt": prompt,
            "stream": False
        }
        json_payload = json.dumps(payload)

        # Send request to Ollama API
        response = requests.post(
            'http://localhost:3000/ollama/api/generate',
            data=json_payload,
            headers=self.headers
        )

        response.raise_for_status()

        # Extract the generated text from Ollama's response
        generated_text = response.json()['response']

        return generated_text

    def generate_cover_letter(self, cv_path, job_description, dropdown):
        """
        Generate cover letter using Ollama via OpenWebUI.

        Args:
            cv_path (str): Path to the CV file.
            job_description (str): Job description provided by the user.

        Returns:
            str: Generated cover letter text or error message if fails.
        """
        model_choice = dropdown
        try:

            # Extract text from CV
            cv_text = self.extract_text(cv_path)

            prompt = f"""
                Here is a CV I would like to ask for your help with:
                --------
                {cv_text}
                ---------
                Please interpret this CV and return it. Do not modify the text, just augment the CV making company names more prominent, time periods of each work experience more prominent, and formatting all around more obvious. 
            """
            cleaned_prompt = clean_prompt(prompt)

            better_cv = self.query_llm(cleaned_prompt,model_choice=model_choice)

            print(f"""--------------------------------
                This is a better CV:
                --------------------
                {better_cv}
                -----------------------------""")
            if len(better_cv)>0:
                return better_cv

            # Create prompt for generating cover letter
            prompt = f"""
                Write a cover letter based on my CV for the job descriptions below. My CV:
                --------
                {better_cv}
                ---------
                and the following job description:
                ---------
                {job_description}
                ---------
                Please write a cover letter based on my above CV for the above job description. Think about what themes might be relevant and use relevant parts of my CV.
                Come up with something creative about why I'm interested in the job itself. 
            """
            cleaned_prompt = clean_prompt(prompt)

            # print(cleaned_prompt)

            # Append current prompt to conversation history
            self.conversation_history.append(cleaned_prompt)

            generated_text = self.query_llm(cleaned_prompt,model_choice=model_choice)

            # Append the generated text to conversation history for future context
            self.conversation_history.append(generated_text)

            return generated_text

        except requests.exceptions.RequestException as e:
            print(f"Error communicating with Ollama API: {e}")
            # return json_payload
            return "Unable to generate cover letter at this time."

    def reset_history(self):
        """
        Reset the conversation history for a new session.
        """
        self.conversation_history = []