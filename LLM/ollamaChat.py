from langchain_ollama.llms import OllamaLLM
from LLM.model_base import ModelBase


class Model(ModelBase):
    def __init__(self, config):
        super().__init__(config)
        self.__model = OllamaLLM(model=self.config)

    def chat(self, prompt):
        return self.__model
    
