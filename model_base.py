class ModelBase:
    def __init__(self, config):
        self.config = config

    def chat(self, prompt):
        raise NotImplementedError
    
    def unload_model(self):
        pass
    