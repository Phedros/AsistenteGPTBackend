import gpt_manager


class Flow:
    def __init__(self, id=None, name=None, agent_list=None):
        self.id = id
        self.name = name
        self.agent_list = agent_list if agent_list is not None else []

    def process_flow(self, prompt):
        results = []
        for agent in self.agent_list:
            result = agent.get_chat_response(prompt)
            results.append(result)
        return results
    
   

