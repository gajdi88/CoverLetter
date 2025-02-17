import requests
from dotenv import load_dotenv
import re
import os
import json
from docx import Document

load_dotenv()


def clean_prompt(prompt: str) -> str:
    """
    Cleans the input prompt by removing special characters that might cause issues in JSON or API requests.
    This function:
      - Removes any characters that are not alphanumeric, whitespace, or basic punctuation (. , : ; ? ! ' " -)
      - Collapses multiple spaces into one.
    """
    cleaned = re.sub(r'[^A-Za-z0-9\s\.\,\:\;\?\'\"\!\-]', '', prompt)
    cleaned = re.sub(r'[ \t\r\f+]', ' ', cleaned).strip()
    cleaned = re.sub(r'\n\s+', '\n', cleaned).strip()
    return cleaned


class CoverLetterGenerator:
    def __init__(self):
        self.conversation_history = []
        api_key = os.environ.get("API_KEY")
        self.headers = {"Authorization": f"Bearer {api_key}"}
        # Local endpoint (default provider)
        self.ollama_url = "http://localhost:3000/ollama/api/generate"
        # Option for Together.ai hosted models; set via environment variable if needed
        self.together_url = os.environ.get("TOGETHER_API_URL", "https://api.together.ai/generate")
        print(self.headers)

    def get_model_ids(self):
        """
        Fetch available model IDs from the API endpoint.
        Returns a list of model IDs or a default list if the API call fails.
        """
        url = "http://localhost:3000/api/models"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            models_data = response.json()["data"]
            # Extract model IDs from the API response.
            model_ids = [model["id"] for model in models_data if "id" in model]
            return model_ids
        except Exception as e:
            print(f"Error fetching models: {e}")
            # Fallback default list.
            return ["deepseek-r1:32b", "phi4:14b", "qwen:32b", "llama3.2:3b"]

    def extract_text(self, cv_path):
        """
        Extract text from a CV file (DOCX).
        """
        doc = Document(cv_path)
        raw_text = [para.text for para in doc.paragraphs]
        return '\n'.join(raw_text)

    def query_llm(self, prompt, model_choice, provider="ollama"):
        """
        Query the language model API.

        Args:
            prompt (str): The prompt to send.
            model_choice (str): The model name (e.g., "deepseek-r1:32b").
            provider (str): Which provider to use ("ollama" or "together").
        """
        payload = {
            "model": model_choice,
            "prompt": prompt,
            "stream": False
        }
        json_payload = json.dumps(payload)

        # Choose the appropriate endpoint based on provider.
        if provider.lower() == "together":
            url = self.together_url
        else:
            url = self.ollama_url

        response = requests.post(url, data=json_payload, headers=self.headers)
        response.raise_for_status()
        generated_text = response.json()['response']
        return generated_text

    def generate_cover_letter(self, cv_path, job_description, model_choice,
                              summarise_cv=True, summarise_job=True):
        """
        Generate a cover letter using the specified model.

        Args:
            cv_path (str): Path to the CV file.
            job_description (str): The job description text.
            model_choice (str): The model to use (passed from the dropdown).
            summarise_cv (bool): Whether to summarise/format the CV.
            summarise_job (bool): Whether to summarise/format the job description.

        Returns:
            str: The generated cover letter.
        """
        try:
            # Extract raw CV text
            cv_text = self.extract_text(cv_path)

            # Optionally summarise the CV
            if summarise_cv:
                prompt_cv = f"""
                Here is a CV I would like to ask for your help with:
                --------
                {cv_text}
                ---------
                Please shorten this CV and highlight more recent experience. Enhance the formatting by making company names and time periods more prominent.
                Do not include any extra comments.
                """
                cleaned_prompt_cv = clean_prompt(prompt_cv)
                cv_text = self.query_llm(cleaned_prompt_cv, model_choice)

            # Optionally summarise the job description
            if summarise_job:
                prompt_job = f"""
                Here is a job description:
                --------
                {job_description}
                ---------
                Please summarise and shorten it without any comments.
                """
                cleaned_prompt_job = clean_prompt(prompt_job)
                job_description = self.query_llm(cleaned_prompt_job, model_choice)

            # Create the cover letter prompt using the (optionally) processed inputs
            prompt_cover = f"""
            Write a cover letter based on the following CV and job description.
            CV:
            --------
            {cv_text}
            ---------
            Job Description:
            ---------
            {job_description}
            ---------
            Please craft a creative cover letter that highlights relevant experience from the CV and demonstrates enthusiasm for the job.
            """
            cleaned_prompt_cover = clean_prompt(prompt_cover)
            self.conversation_history.append(cleaned_prompt_cover)
            cover_letter = self.query_llm(cleaned_prompt_cover, model_choice)
            self.conversation_history.append(cover_letter)
            return cover_letter
        except requests.exceptions.RequestException as e:
            print(f"Error communicating with API: {e}")
            return "Unable to generate cover letter at this time."

    def reset_history(self):
        """
        Reset the conversation history.
        """
        self.conversation_history = []
