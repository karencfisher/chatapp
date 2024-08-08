from pathlib import Path
import json
import os
import importlib
import tiktoken

from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain.schema import StrOutputParser
from langchain.tools import Tool
from langchain_community.chat_message_histories import FileChatMessageHistory
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.messages import messages_to_dict


class FileChatMessageHistoryTrim(FileChatMessageHistory):
    """Overriding behavior in the parent class to return messages within
       a limited context window"""
    def __init__(self, file_path, limit):
        super().__init__(file_path)
        self.limit = limit

    @property
    def messages(self):
        messages = super().messages
        messages_trimmed = self.__get_trimmed_messages(messages)
        return messages_trimmed
    
    def add_message(self, message):
        messages_saved = super().messages
        messages = messages_to_dict(messages_saved)
        messages.append(messages_to_dict([message])[0])
        self.file_path.write_text(json.dumps(messages))
    
    def __get_trimmed_messages(self, messages):
        encoder = tiktoken.get_encoding('p50k_base')
        trimmed_messages = []
        token_count = 0
        for message in messages[::-1]:
            token_count += len(encoder.encode(message.content))
            if token_count > self.limit:
                break
            trimmed_messages.insert(0, message)
        return trimmed_messages


class Agents:
    def __init__(self):
        self.__agents = {}

    def add_agent(self, user_profile):
        new_agent = Chat(user_profile)
        self.__agents[user_profile['username']] = new_agent

    def remove_agent(self, username):
        if self.__agents.get(username, None) is not None:
            del self.__agents[username]

    def __get_agent(self, username):
        return self.__agents[username]
    
    def get_model(self, username):
        return self.__get_agent(username).get_model()
    
    def get_conversation(self, username):
        return self.__get_agent(username).get_conversation()
    
    def chat(self, username, message):
        return self.__get_agent(username).chat(message)
    
    def clear_session(self, username):
        self.__get_agent(username).clear_session()
        

class Chat:
    def __init__(self, user_profile):
        self.user_profile = user_profile
        with open(Path('Chat/model_config.json'), 'r') as FILE:
            self.config = json.load(FILE)

        with open(Path('Chat/persona.txt'), 'r') as FILE:
            self.persona = FILE.read()

        with open(Path('Chat/instructions.txt'), 'r') as FILE:
            self.instructions = FILE.read()

        if os.path.exists(Path('Chat/tools.py')):
            self.tools = importlib.import_module("Chat.tools")
        else:
            self.tools = None

        print(f'Loading model {self.config["model"]}...')
        provider = importlib.import_module(f"LLM.{self.config['provider'].strip()}")
        self.model = provider.Model(self.config)
        self.__init_agent()

    def __init_agent(self):
        profile = f'\nUser Profile:\nname: {self.user_profile["name"]}\n \
                    location: {self.user_profile["location"]}\n'
        self.persona += profile
        chat_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.persona),
                ("human", "{input}")
            ]
        )   
        basic_chat = chat_prompt | self.model.chat() | StrOutputParser()

        tools = [
            Tool.from_function(
                name="General Chat",
                description="For general chat not covered by other tools",
                func=basic_chat.invoke
            )
        ]

        if self.tools is not None:
            for tool in self.tools.tools:
                new_tool = Tool.from_function(
                    name=tool['name'],
                    description=tool['description'],
                    func=tool['func']
                )
                tools.append(new_tool)

        instructions = f'{self.persona}\n\n{self.instructions}'
        agent_prompt = PromptTemplate.from_template(instructions)
        agent = create_react_agent(self.model.chat(), tools, agent_prompt)
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            handle_parsing_errors=True
        )

        def get_memory(session_id):
            limit = self.config['context_window'] - self.config['max_response']
            conversation = FileChatMessageHistoryTrim(Path(f'Conversations/{session_id}.json'),
                                                      limit)
            return conversation

        self.chat_agent = RunnableWithMessageHistory(
            agent_executor,
            get_memory,
            input_messages_key="input",
            history_messages_key="chat_history"
        )

    def get_model(self):
        return self.config['model']

    def get_conversation(self):
        history = FileChatMessageHistory(Path(f'Conversations/{self.user_profile["username"]}.json'))
        conversation = []
        for item in history.messages:
            message = {}
            if isinstance(item, HumanMessage):
                message['role'] = 'human'
            else:
                message['role'] = 'ai'
            message['content'] = item.content
            conversation.append(message)
        return conversation

    def chat(self, message):
        response = self.chat_agent.invoke(
            {"input": message},
            {"configurable": {"session_id": self.user_profile['username']}}
        )
        return response['output']

    def clear_session(self):
        history = FileChatMessageHistory(Path(f'Conversations/{self.user_profile["username"]}.json'))
        history.clear()
