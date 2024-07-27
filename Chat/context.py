'''
Maintain context buffer for ChatGPT.

There are two sections:

PRETEXT: a description of the chatbot
CONTEXT: the current conversation

The maximum length of the buffer is 4096 tokens. We will deduct the
length of the pretext, and the maximum tokens for a response. When
queried for the current context, will will return messages from
the most recent until fitting within the difference.

'''
import tiktoken as tt


class Contexts:
    def __init__(self):
        self.contexts = {}

    def init_context(self, session_id, pretext, num_response_tokens, max_context_tokens):
        self.contexts[session_id] = Context(pretext, num_response_tokens, max_context_tokens)

    def __retrieve_context(self, session_id):
        context = self.contexts.get(session_id)
        if context is None:
            raise ValueError("Invalid session_id")
        return context

    def get_context(self, session_id):
        return self.__retrieve_context(session_id).get_context()
    
    def get_full_conversation(self, session_id):
        return self.__retrieve_context(session_id).get_full_conversation()
    
    def add(self, session_id, role, text):
        self.__retrieve_context(session_id).add(role, text)

    def clear_session(self, session_id):
        self.__retrieve_context(session_id).clear()


class Context:
    def __init__(self, pretext, num_response_tokens, max_context_tokens):
        self.__max_context_tokens = max_context_tokens
        self.__num_response_tokens = num_response_tokens
        self.__context = []
        self.__pretext = []

        # get system prompt (pretext)
        self.__encoder = tt.get_encoding('p50k_base')
        self.__num_pretext_tokens = len(self.__encoder.encode(pretext))
        self.__pretext.append({'role': 'system', 'content': pretext})
        self.__max_conv = (self.__max_context_tokens - 
                           (self.__num_pretext_tokens + self.__num_response_tokens))

    def get_context(self):
        '''
        Manage the context capacity as well as returning the 
        combined pretext and context
        '''
        # encode the context, and truncate early portion as needed
        # to keep within limit
        n_tokens = 0
        context = []
        for index in range(len(self.__context) - 1, -1, -1):
            n_tokens += self.__context[index]['n_tokens']
            if n_tokens >= self.__max_conv:
                break
            context.append(self.__context[index]['message'])

        # return concatenated pretext and context
        return self.__pretext + context[::-1]
    
    def get_full_conversation(self):
        conversation = [message['message'] for message in self.__context]
        return conversation
        
    def add(self, role, text):
        '''
        Add token count, role, and content to the context

        Input: new text
        '''
        if len(text) > 0:
            # if not passed, estimate number of tokens
            n_tokens = len(self.__encoder.encode(text))
            message = {'n_tokens': n_tokens, 
                       'message': {'role': role, 'content': text}}
            self.__context.append(message)

    def clear(self):
        self.__context = []
