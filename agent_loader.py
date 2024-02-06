import json


class AgentLoader:

  def __init__(self):
    self.agents = self.load_agents()

  def get_agent_names(self):
    return self.agents.keys()

  def load_agents(self):
    agents = {}
    with open("agents/agents.json") as f:
      agents_data = json.load(f)
      for agent in agents_data:
        agents[agent["id"]] = agent
    return agents

  def get_agent(self, id, case_sensitive=False):
    if case_sensitive:
        return self.agents.get(id)
    else:
        
        for agent_id, agent_details in self.agents.items():
            if agent_id.lower() == id.lower():
                return agent_details
        return None

  def is_agent_email(self, email):
    """Check if the given email belongs to one of the agents."""
    return bool(self.get_agent_by_email(email))

  def get_agent_persona(self, id, case_sensitive=False):
    agent = self.get_agent(id, case_sensitive)
    if agent:
      persona = agent.get("persona", None)
      # print(f"Debug: AgentLoader.get_agent_persona('{id}') returned: {persona}")
      return persona
    else:
      print(f"Debug: AgentLoader.get_agent_persona('{id}') found no agent.")
      return None

  def get_agent_by_email(self, email):
    local_part = email.split('@')[0].lower()
    for agent_id, agent in self.agents.items():
      if agent_id.lower() == local_part:
        return agent
    return None
