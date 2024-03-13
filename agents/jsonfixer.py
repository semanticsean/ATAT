import json

# Load the JSON data from 'agents.json'
with open('agents.json', 'r') as file:
    agents = json.load(file)

# Function to convert the devLarry-like structure to devRocket-like
def convert_structure(agent):
    # Convert 'keywords' if it is a dictionary (like in devLarry)
    if isinstance(agent['keywords'], dict):
        agent['keywords'] = list(agent['keywords'].values())

    # Convert 'relationships' if it is not formatted as expected
    if isinstance(agent['relationships'], list) and len(agent['relationships']) == 1 and isinstance(agent['relationships'][0], dict):
        new_relationships = []
        for key, relationship in agent['relationships'][0].items():
            new_relationships.append(relationship)
        agent['relationships'] = new_relationships

# Apply conversion to each agent
for agent in agents:
    convert_structure(agent)

# Save the modified data back to 'agents.json'
with open('agents_modified.json', 'w') as file:
    json.dump(agents, file, indent=4)

# Inform user of completion
print("All records have been checked and reformatted as necessary. The modified data is saved in 'agents_modified.json'.")
