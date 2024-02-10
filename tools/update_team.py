import os
import openai
import glob
import time

# Load environment variables
openai.api_key = os.getenv("OPENAI_API_KEY")
company_name = os.getenv("COMPANY_NAME", "Your Default Company Name")


def rewrite_file_content(original_text,
                         transformation_prompt,
                         max_tokens=1000):
  """Uses GPT to rewrite the file content based on the user's prompt and company context."""
  additional_instructions = f" Ensure the new content aligns with the identity and services of {company_name}, an ad agency. Keep the format but change character names and details to fit the new context. Place the agent's name on the first line followed by two line breaks. Only the name should be on the first line, without labels or additional text.THE NAME MUST BE THE FIRST LINE. Follow the name with two line breaks before proceeding with the content.YOU ARE MAKING A ROLEPLAYING AI AGENT. YOU ARE NOT MAKING A COMPANY. THE NEW AGENT WORKS FOR OR WITH THE COMPANY."
  messages = [{
      "role": "system",
      "content": "You are a highly creative assistant. "
  }, {
      "role":
      "user",
      "content":
      f"{transformation_prompt} Original text: {original_text} {additional_instructions}"
  }]

  response = openai.ChatCompletion.create(model="gpt-3.5-turbo",
                                          messages=messages,
                                          max_tokens=max_tokens,
                                          temperature=0.7,
                                          top_p=1.0,
                                          frequency_penalty=0,
                                          presence_penalty=0)

  time.sleep(10)
  return response.choices[-1].message['content'].strip()


def process_files(directory, transformation_prompt, num_files=None):
  text_files = glob.glob(f'{directory}/*.txt')
  print(f"Found {len(text_files)} text files to process.")  # Debugging log

  for file_path in text_files:
    print(f"Processing {file_path}...")  # Debugging log
    try:
      with open(file_path, 'r') as file:
        original_text = file.read()
      rewritten_text = rewrite_file_content(original_text,
                                            transformation_prompt)
      with open(file_path, 'w') as file:
        file.write(rewritten_text)
      print(f"Successfully processed {file_path}.")  # Debugging log
    except Exception as e:
      print(f"Error processing {file_path}: {e}")  # Error handling

  print("Completed processing all files with update_team.")


def create_new_agent_files(directory, num_new_agents, transformation_prompt):
  # Determine the starting index for new files based on existing files
  existing_files = glob.glob(f'{directory}/*.txt')
  start_index = len(existing_files) + 1

  for i in range(start_index, start_index + num_new_agents):
    new_file_path = os.path.join(directory, f'agent_{i}.txt')
    with open(new_file_path, 'w') as new_file:

      original_text = "Agent Name {i}\n\nGeneric Description: This agent is designed to excel in various tasks. {transformation_prompt} Agent Name: Start with the agent's name at the top, such as 'John Doe'. Place the agent's name on the first line followed by two line breaks. Only the name should be on the first line, without labels or additional text.THE NAME MUST BE THE FIRST LINE. Follow the name with two line breaks before proceeding with the content. Professional Background: Job Title: Assign an appropriate title reflecting the agent's role.Field of Expertise: Specify the area of specialization. Character Disposition: Describe the agent's general temperament.Company Associations: Primary Company: Name the main company and detail the agent's role within it, including a brief description of the company's operations. Associated Company: If applicable, name another company the agent is linked to, describing the relationship and summarizing the company's focus. Products and Services: Offer a succinct overview of what the agent provides or is involved with. Personal Attributes: Emotional Processing: Briefly describe their emotional characteristics Memory Processing: Outline how they handle memory. Decision-making: Explain their approach to making decisions Social Interactions: Describe their social interaction skills and understanding. Anticipation of Behavior: Detail how they predict others' actions. Action Guidance: Clarify the principles or beliefs guiding their actions. Narrative Experiences: Highlight any significant stories or experiences shaping their worldview. Vision and Philosophy: Share their future outlook and philosophical stance. Collaborations: Describe key relationships and collaborations, focusing on the nature and impact of these connections.Goals and Objectives: Concisely state their primary aims and ambitions."
      rewritten_text = rewrite_file_content(original_text,
                                            transformation_prompt)
      new_file.write(rewritten_text)
      print(f"New agent file created: {new_file_path}")


def update_team(directory, transformation_prompt, num_agents):
  process_files(directory, transformation_prompt,
                None)  # Process all existing files without limiting the number

  if num_agents is not None and num_agents > 0:
    create_new_agent_files(directory, num_agents, transformation_prompt)


if __name__ == "__main__":
  directory = input(
      "Enter the directory of agent files (default 'agents/new_agent_files'): "
  ) or "agents/new_agent_files"
  transformation_prompt = input(
      "Enter your transformation prompt (e.g., 'make it an ad agency'): ")
  num_agents = input(
      "Enter the number of agents to generate (press enter process files in /agents/new_agent_files): "
  )
  num_agents = int(num_agents) if num_agents.isdigit() else 0

  update_team(directory, transformation_prompt, num_agents)
