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
        Also appends a Together.ai model option.
        """
        url = "http://localhost:3000/api/models"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            models_data = response.json()["data"]
            model_ids = [model["id"] for model in models_data if "id" in model]
        except Exception as e:
            print(f"Error fetching models: {e}")
            model_ids = ["deepseek-r1:32b", "phi4:14b", "qwen:32b", "llama3.2:3b"]

        # Append Together.ai model option (using the prefix "together:" for identification).
        model_ids.append("together:deepseek-ai/DeepSeek-V3")
        return model_ids

    def extract_text(self, cv_path):
        """
        Extract text from a CV file (DOCX).
        """
        doc = Document(cv_path)
        raw_text = [para.text for para in doc.paragraphs]
        return '\n'.join(raw_text)

    def query_llm(self, prompt, model_choice):
        """
        Query the language model API.
        If the model_choice starts with "together:", use the Together.ai client.
        Otherwise, use the default Ollama endpoint.
        """
        if model_choice.startswith("together:"):
            # Extract the actual model name after the "together:" prefix.
            together_model = model_choice.split("together:")[1]
            try:
                from together import Together
            except ImportError:
                raise ImportError("Please install the together package to use Together.ai models.")
            client = Together()
            messages = [{"role": "user", "content": prompt}]
            response = client.chat.completions.create(
                model=together_model,
                messages=messages,
                max_tokens=None,
                temperature=0.7,
                top_p=0.7,
                top_k=50,
                repetition_penalty=1,
                stop=["<｜end▁of▁sentence｜>"],
                stream=True
            )
            generated_text = ""
            try:
                for token in response:
                    if hasattr(token, 'choices') and token.choices:
                        choice = token.choices[0]
                        if hasattr(choice, 'delta') and getattr(choice.delta, 'content', None):
                            generated_text += choice.delta.content
            except:
                print("Error: Issue with response from Together.ai")
            return generated_text
        else:
            payload = {
                "model": model_choice,
                "prompt": prompt,
                "stream": False
            }
            json_payload = json.dumps(payload)
            response = requests.post(self.ollama_url, data=json_payload, headers=self.headers)
            response.raise_for_status()
            generated_text = response.json()['response']
            return generated_text

    def generate_cover_letter(self, cv_path, job_description, model_choice,
                              summarise_cv_job=True):
        """
        Generate a cover letter using the specified model.
        """
        try:
            # Extract raw CV text.
            cv_text = self.extract_text(cv_path)

            # Optionally summarise the CV.
            if summarise_cv_job:
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

            # Optionally summarise the job description.
            if summarise_cv_job:
                prompt_job = f"""
                Here is a job description:
                --------
                {job_description}
                ---------
                Please summarise and shorten it without any comments.
                """
                cleaned_prompt_job = clean_prompt(prompt_job)
                job_description = self.query_llm(cleaned_prompt_job, model_choice)

            # Create the cover letter prompt using the (optionally) processed inputs.
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
