from pathlib import Path
import json
import os
import importlib

from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain.schema import StrOutputParser
from langchain.tools import Tool
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.messages import HumanMessage, AIMessage

from Chat.chat_history import FileChatHistory


class Agents:
    def __init__(self):
        self.__agents = {}

    def add_agent(self, user_profile):
        new_agent = Agent(user_profile)
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
        

class Agent:
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

        limit = self.config['context_window'] - self.config['max_response']
        chat_path = Path(f'Conversations/{self.user_profile["username"]}.json')
        self.conversation = FileChatHistory(chat_path, limit)
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

        self.chat_agent = RunnableWithMessageHistory(
            agent_executor,
            lambda session_id: self.conversation,
            input_messages_key="input",
            history_messages_key="chat_history"
        )

    def get_model(self):
        return self.config['model']

    def get_conversation(self):
        conversation = []
        for item in self.conversation.full_messages:
            message = {}
            if isinstance(item, HumanMessage):
                message['role'] = 'human'
                item_content = json.loads(item.content)
                message['content'] = item_content['content']
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
        self.conversation.clear()
