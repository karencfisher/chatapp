import os
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from LLM.model_base import ModelBase


class Model(ModelBase):
    def __init__(self, config):
        super().__init__(config)
        load_dotenv()
        self.__client = ChatGroq(api_key=os.getenv('GROQ_API_KEY'),
                               model_name=self.config['model'],
                               temperature=self.config['temperature'])

    def chat(self):
        return self.__client
        
