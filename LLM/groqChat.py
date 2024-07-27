import os
from groq import Groq
from dotenv import load_dotenv
from LLM.model_base import ModelBase


class Model(ModelBase):
    def __init__(self, config):
        super().__init__(config)
        load_dotenv()
        self.client = Groq(api_key=os.getenv('GROQ_API_KEY'))

    def chat(self, prompt):
        response = self.client.chat.completions.create(model=self.config['model'], 
                                                       messages=prompt,
                                                       max_tokens=self.config["max_response"],
                                                       temperature=self.config['temperature'])
        return response.choices[0].message.content
