import json
import os

from context import Context
import importlib


class Chat:
    def __init__(self):
        self.stdio = False
        
        with open('model_config.json', 'r') as CONFIG_FILE:
            self.config = json.load(CONFIG_FILE)
        
        # get system prompt
        if os.path.exists('chat_system_prompt.txt'):
            with open('chat_system_prompt.txt', 'r') as PRETEXT:
                self.pretext = PRETEXT.read()
        else:
                self.pretext = "You are a helpful chatbot."
        
        # concatinate user profile if one exists
        if os.path.exists('chat_user_profile.txt'):
            with open('chat_user_profile.txt', 'r') as PROFILE:
                profile = PROFILE.read()
            self.pretext += 'User profile:\n\n' + profile
        
        # setup conversation context
        self.context = Context(self.pretext, 
                               num_response_tokens=self.config['max_response'],
                               max_context_tokens=self.config['context_window'])

        # load or connect to model
        print(f'Loading model {self.config["model"]}...')
        provider = importlib.import_module(self.config['provider'].strip())
        self.model = provider.Model(self.config)
        print('Done!')

    def getModel(self):
        return self.config["model"]

    def __addContext(self, role, text):
        self.context.add(role=role, 
                         text=text)
        
    def __getContext(self):
        return self.context.get_context()
    
    def get_conversation(self):
        return self.context.get_full_conversation()

    def chat(self, message):
        self.__addContext('user', message)
        prompt = self.__getContext()
        ai_message = self.model.chat(prompt)
        self.__addContext('assistant', ai_message)
        return ai_message
    
    def closeServer(self):
        print('Closing model...')
        self.model.unload_model()
        print('Done!')
