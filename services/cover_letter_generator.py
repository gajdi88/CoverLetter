# services/cover_letter_generator.py

import requests


class CoverLetterGenerator:
    def __init__(self):
        self.conversation_history = []
        self.headers = {"Authorization": "Bearer XXXXXXXTOKENXXXXXX"}

    def extract_text(self, cv_path):
        """
        Extract text from CV file.
        Implement actual extraction logic here.
        """
        return "sample cv text"

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
            prompt = f"Write a cover letter based on this CV: {cv_text} and the following job description: {job_description}"

            # Append current prompt to conversation history
            self.conversation_history.append(prompt)

            # Prepare messages for Ollama API request
            messages = [{"role": "user", "content": msg} for msg in self.conversation_history]

            test_message = '''
            {
              "model": "deepseek-r1:32b",
              "prompt": "What's the capital of Australia?",
              "stream": false
            }
            '''

            # Send request to Ollama API
            response = requests.post(
                'http://localhost:3000/ollama/api/generate',
                data=test_message,
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