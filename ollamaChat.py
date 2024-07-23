import ollama
from model_base import ModelBase


class Model(ModelBase):
    def __init__(self, config):
        super().__init__(config)
        ollama.chat(model=self.config['model'], 
                    keep_alive=-1,
                    options={'num_ctx': self.config['context_window']})

    def chat(self, prompt):
        response = ollama.chat(model=self.config['model'], messages=prompt)
        ai_message = response['message']['content']
        return ai_message
    
    def unload_model(self):
        ollama.chat(model=self.config['model'], keep_alive=0)
