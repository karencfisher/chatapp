import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from LLM.model_base import ModelBase


class Model(ModelBase):
    def __init__(self, config):
        super().__init__(config)
        load_dotenv()
        self.__client = ChatOpenAI(
            api_key=os.getenv('OPENAI_API_KEY'),
            model=self.config['model'],
            temperature=self.config['temperature'],
            max_tokens=config['max_response']
        )

    def chat(self):
        return self.__client
        
