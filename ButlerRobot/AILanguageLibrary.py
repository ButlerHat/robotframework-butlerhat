import os
import requests
from robot.api.deco import keyword
from robot.libraries.BuiltIn import BuiltIn


class AILanguageLibrary:
    """
    AILanguageLibrary is a Robot Framework library for interacting with AI language models.
    """
    ROBOT_LIBRARY_SCOPE = 'GLOBAL'

    def __init__(self, ai_url=None, console=False):
        API_URL = "https://api-inference.huggingface.co/models/google/flan-t5-large"
        # Hugging face API Token
        self.hf_token = os.environ.get('HF_TOKEN', None)
        self.ai_url = ai_url  if ai_url is not None else API_URL
        self.console = console


    # ======= Task Keywords =======	 
    @keyword("Ask T5: ${question}")
    def ask(self, question):
        headers = {"Authorization": f"Bearer {self.hf_token}"}

        def query(payload):
            response = requests.post(self.ai_url, headers=headers, json=payload)
            return response.json()
        
        BuiltIn().log(f"Waiting for T5 response for question.", level='DEBUG', console=self.console)
        output = query({
            "inputs": question,
            "options": {
                "wait_for_model": True
            }
        })
        if isinstance(output, list):
            output = output[0]
        if 'generated_text' not in output:
            BuiltIn().log(f"Error in T5 response: {output}", level='WARN', console=self.console)
            return False
        result = output['generated_text'].strip()
        BuiltIn().log(f"T5 response {result}", level='DEBUG', console=self.console)
        return result