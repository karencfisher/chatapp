import json
import os
import importlib
from pathlib import Path

from Chat.context import Contexts


class Chat:
    def __init__(self):
        self.stdio = False
        
        with open(Path('Chat/model_config.json'), 'r') as CONFIG_FILE:
            self.config = json.load(CONFIG_FILE)
        
        # get system prompt
        if os.path.exists(Path('Chat/chat_system_prompt.txt')):
            with open(Path('Chat/chat_system_prompt.txt'), 'r') as PRETEXT:
                self.pretext = PRETEXT.read()
        else:
                self.pretext = "You are a helpful chatbot."
        
        # concatinate user profile if one exists
        if os.path.exists(Path('Chat/chat_user_profile.txt')):
            with open(Path('Chat/chat_user_profile.txt'), 'r') as PROFILE:
                profile = PROFILE.read()
            self.pretext += 'User profile:\n\n' + profile
        
        # setup conversation contexts
        self.contexts = Contexts()

        # load or connect to model
        print(f'Loading model {self.config["model"]}...')
        provider = importlib.import_module(f"LLM.{self.config['provider'].strip()}")
        self.model = provider.Model(self.config)
        print('Done!')

    def getModel(self):
        return self.config["model"]

    def __addContext(self, session_id, role, text):
        self.contexts.add(session_id, role, text)
        
    def __getContext(self, session_id):
        return self.contexts.get_context(session_id)
    
    def get_conversation(self, session_id):
        try:
            return self.contexts.get_full_conversation(session_id)
        except ValueError:
            self.contexts.init_context(session_id, 
                                      self.pretext, 
                                      self.config['max_response'],
                                      self.config['context_window'])
            return []

    def chat(self, session_id, message):
        self.__addContext(session_id, 'user', message)
        prompt = self.__getContext(session_id)
        ai_message = self.model.chat(prompt)
        self.__addContext(session_id, 'assistant', ai_message)
        return ai_message
    
    def clear_session(self, session_id):
        self.contexts.clear_session(session_id)
    
    def close_server(self):
        print('Closing model...')
        self.model.unload_model()
        print('Done!')
