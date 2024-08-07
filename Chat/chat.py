from pathlib import Path
import json
import os
import importlib

from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain.schema import StrOutputParser
from langchain.tools import Tool
from langchain_community.chat_message_histories import FileChatMessageHistory
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.messages import HumanMessage, AIMessage


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

        if os.path.exists(Path('Chat/tools.json')):
            with open(Path('Chat/tools.json'), 'r') as FILE:
                self.tools = json.load(FILE)
        else:
            self.tools = []

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

        for tool in self.tools:
            module = importlib(f'langchain_community.tools import {tool["module"]}')
            new_tool = Tool.from_function(
                name=tool['name'],
                description=tool['description'],
                func=module.run
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
            return FileChatMessageHistory(Path(f'Conversations/{session_id}.json'))

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
        history = FileChatMessageHistory(Path(f'Chat/Conversations/{self.user_profile["username"]}.json'))
        history.clear()
