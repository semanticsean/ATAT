import agent_operator
import json

# Instantiate the AgentSelector class from agent_operator
agent_selector = agent_operator.AgentSelector()

# Sample data to simulate the conversation history
agent_responses = [("Agent1", "agent1@semantic-life.com",
                    "Hello, this is the first message."),
                   ("Agent2", "agent2@semantic-life.com",
                    "This is a reply to the first message."),
                   ("Agent3", "agent3@semantic-life.com",
                    "This is a reply to the second message.")]

# Convert existing history to HTML format if needed
existing_history = None

# Test the format_conversation_history_html method with the sample data
formatted_history = agent_selector.format_conversation_history_html(
    agent_responses, existing_history)

# Save the output to a text file in the current working directory
output_file_path = 'formatted_history.html'
with open(output_file_path, 'w') as file:
  file.write(formatted_history)

# Display the path to the saved output
print(f'Formatted history has been saved to {output_file_path}')
