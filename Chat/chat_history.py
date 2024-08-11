from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import messages_from_dict, messages_to_dict
import tiktoken
import json


class FileChatHistory(BaseChatMessageHistory):
    def __init__(self, file_path, limit):
        self.file_path = file_path
        self.limit = limit
        self.__cache = []
        self.__cache_token_count = 0
        self.__cache_top = 0

        if not self.file_path.exists():
            self.file_path.touch()
            return

        with open (self.file_path, 'r') as FILE:
            for line in FILE:
                raw_message = json.loads(line.strip())
                message = messages_from_dict([raw_message])[0]
                self.add_message(message, write_through=False)
        self.__trim_cache_messages()

    @property
    def messages(self):
        return self.__cache[self.__cache_top:]
    
    @property
    def full_messages(self):
        return self.__cache
        
    def add_message(self, message, write_through=True):
        encoder = tiktoken.get_encoding('p50k_base')
        self.__cache.append(message)
        self.__cache_token_count += len(encoder.encode(message.content))

        if write_through:
            self.__trim_cache_messages()
            with open(self.file_path, 'a') as FILE:
                FILE.write(f'{json.dumps(messages_to_dict([message])[0])}\n')

    def clear(self):
        self.__cache = []
        self.__cache_token_count = 0
        self.__cache_top = 0
        with open(self.file_path, 'r+') as FILE:
            FILE.truncate(0)

    def __trim_cache_messages(self):
        encoder = tiktoken.get_encoding('p50k_base')
        while self.__cache_token_count > self.limit:
            message = self.__cache[self.__cache_top]
            self.__cache_token_count -= len(encoder.encode(message.content))
            self.__cache_top += 1
        