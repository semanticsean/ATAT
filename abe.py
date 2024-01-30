import json
import time
import random
import os
import openai
import csv
import shutil
"""
ABE
A/B+E
A/B Testing + Elections

Create a json, csv, and html from a set of questions and instructions, runs to all agents in /agents/agents.json. 

"""


def load_json_file(file_path):
  """Load JSON data from a file."""
  with open(file_path, 'r') as file:
    return json.load(file)


def save_csv_file(data, file_path):
  """Save data to a CSV file."""
  if not data:
    print("No data to save in CSV.")
    return

  headers = list(data[0]['responses'].keys())

  with open(file_path, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.DictWriter(file, fieldnames=headers)
    writer.writeheader()
    for agent in data:
      # Flatten the response data to match CSV format
      row = {
          question: agent['responses'].get(question, '')
          for question in headers
      }
      writer.writerow(row)


def save_json_file(data, file_path):
  """Save data to a JSON file."""
  with open(file_path, 'w') as file:
    json.dump(data, file, indent=4)


def jitter_delay(base_delay=60, jitter_factor=0.1):
  """Generate a delay with jitter."""
  jitter = random.uniform(-jitter_factor, jitter_factor) * base_delay
  return base_delay + jitter


def exponential_backoff(attempt, base_delay=60, factor=2):
  """Calculate exponential backoff delay."""
  return base_delay * (factor**attempt)


def generate_output_filename():
  """Generate a unique filename for the output JSON file."""
  timestamp = time.strftime("%Y%m%d-%H%M%S")
  return f"output/output_{timestamp}.json"


def generate_unique_html_filename():
  """Generate a unique filename for the HTML file."""
  timestamp = time.strftime("%Y%m%d-%H%M%S")
  return f"generated_page_{timestamp}.html"


def create_unique_output_folders():
  """Create unique output folders and return their paths."""
  timestamp = time.strftime("%Y%m%d-%H%M%S")
  base_folder = os.path.join('abe/results', f'unique_folder_{timestamp}')
  data_folder = os.path.join(base_folder, 'data')
  pics_folder = os.path.join(base_folder, 'pics')
  os.makedirs(data_folder, exist_ok=True)
  os.makedirs(pics_folder, exist_ok=True)
  return base_folder, data_folder, pics_folder


def parse_responses(response, unique_id):
  """Parse the responses from the API call into a dictionary."""
  print(f'Processing agent: {unique_id}')
  try:
    # Ensure the response content is properly formatted for JSON
    response_content = response.choices[0].message.content
    # Replace common problematic characters
    response_content = response_content.replace('\n', '\\n').replace(
        '\r', '\\r').replace('\t', '\\t')
    parsed_response = json.loads(response_content)
    return parsed_response
  except Exception as e:
    print(f'Error encountered while parsing response for {unique_id}: {e}')
    return {"error": f"Error while parsing: {e}"}


def synthetic_poll(agents, questions, instructions, data_folder):
  client = openai.OpenAI(api_key=os.environ['OPENAI_API_KEY'])
  print('OpenAI client initialized.')
  responses = []
  output_json_path = os.path.join(
      data_folder, f"output_{time.strftime('%Y%m%d-%H%M%S')}.json")

  print('Starting agent processing...')
  for agent in agents:
    persona_instruction = agent.get("persona", "")
    summary = agent.get("summary", "")
    keywords = agent.get("keywords", [])
    agent_id = agent.get("id", "")
    model = agent.get("model", "gpt-4")  # Assuming default model is gpt-4
    unique_id = agent.get("unique_id", "unknown_id")

    # Format instructions with agent details
    formatted_instructions = instructions.format(id=agent_id,
                                                 persona=persona_instruction,
                                                 summary=summary,
                                                 keywords=', '.join(keywords))

    # Construct the message for API call
    message_content = json.dumps({
        "instructions": formatted_instructions,
        "questions": questions
    })
    messages = [{"role": "system", "content": message_content}]

    print(f'Processing agent: {unique_id}')
    try:
      response = client.chat.completions.create(model=model, messages=messages)
      parsed_responses = parse_responses(response, unique_id)
      if "error" in parsed_responses:
        print(f'Skipping agent {unique_id} due to error.')
        continue  # Skip this agent if an error occurs in parsing
    except Exception as e:
      print(f'Error encountered: {e}')
      print(f"Error for agent {unique_id}: {e}")
      continue

    response_entry = {
        "id": agent.get("id", ""),
        "email": agent.get("email", ""),
        "persona": persona_instruction,
        "unique_id": unique_id,
        "timestamp": agent.get("timestamp", ""),
        "summary": agent.get("summary", ""),
        "keywords": agent.get("keywords", []),
        "image_prompt": agent.get("image_prompt", ""),
        "photo_path": agent.get("photo_path", ""),
        "instructions": formatted_instructions,
        "responses": parsed_responses,
        "output_filename": output_json_path
    }
    print(f'Appending response for agent: {unique_id}')
    responses.append(response_entry)
    print(f'Saving responses to {output_json_path}')
    save_json_file(responses, output_json_path)

    csv_output_json_path = output_json_path.replace('.json', '.csv')
    print(f'Saving responses to {csv_output_json_path}')
    save_csv_file(responses, csv_output_json_path)
    time.sleep(jitter_delay())

  save_json_file(responses, output_json_path)
  csv_output_json_path = output_json_path.replace('.json', '.csv')
  save_csv_file(responses, csv_output_json_path)

  print('Processing complete.')
  return output_json_path


def copy_images_to_local(data, base_source_folder, target_folder):
  """Copy images from the source to the target folder."""
  for agent in data:
    # Combine base source folder with photo_path from the agent's data
    source_image_path = os.path.join(base_source_folder, agent['photo_path'])
    target_image_path = os.path.join(target_folder,
                                     os.path.basename(agent['photo_path']))

    # Print the source and target paths for confirmation
    print(f"Source image path: {source_image_path}")
    print(f"Target image path: {target_image_path}")

    # Check if source file exists and then copy
    if os.path.exists(source_image_path):
      print(f"Copying image from {source_image_path} to {target_image_path}")
      shutil.copy(source_image_path, target_image_path)
    else:
      print(f"Source file not found: {source_image_path}")


def generate_static_html_page(data, base_folder, data_folder, pics_folder,
                              output_file):
  """Generate a static HTML page with agent data."""

  html_file_path = os.path.join(base_folder, generate_unique_html_filename())
  html_content = "<!DOCTYPE html><html><head><title>Agent Profiles</title></head><body>"

  # Container styling
  container_style = "style='max-width: 640px; margin: auto; padding: 20px;'"

  # Styling for each agent's section
  section_style = "style='border: 1px solid #ddd; padding: 20px; margin-bottom: 20px; border-radius: 8px;'"

  # Responsive image styling
  img_style = "style='max-width: 100%; height: auto; border-radius: 8px;'"

  html_content += f"<div class='container' {container_style}>"

  for agent in data:
    agent_html = f'''
        <div {section_style}>
            <h1>{agent["id"]}</h1>
            <img src='pics/{os.path.basename(agent["photo_path"])}' alt='Profile Photo' class='profile-photo' {img_style}>
            <h2>Questions and Answers</h2>
        '''
    for question, answer in agent["responses"].items():
      if isinstance(answer, str):
        # Replace newline characters with HTML line breaks if answer is a string
        formatted_answer = answer.replace("\n", "<br>")
      else:
        # Otherwise, convert non-string answer to string (e.g., if it's a dictionary)
        formatted_answer = json.dumps(answer, indent=2).replace("\n", "<br>")
      agent_html += f"<div class='qa-section'><p class='question'>{question}</p><p>{formatted_answer}</p></div>"
    agent_html += "</div>"
    html_content += agent_html

  # Add download links for JSON and CSV files
  output_json = os.path.join(data_folder, os.path.basename(output_file))
  output_csv = output_json.replace('.json', '.csv')
  html_content += f"<a href='../{output_json}'>Download JSON</a> "
  html_content += f"<a href='../{output_csv}'>Download CSV</a>"

  html_content += "</div></body></html>"

  with open(html_file_path, 'w') as html_file:
    html_file.write(html_content)
  print(f'Static HTML page saved to {html_file_path}')


def main():
  # Create unique output folders
  base_folder, data_folder, pics_folder = create_unique_output_folders()

  # Load data
  agents = load_json_file('agents/agents.json')
  questions = load_json_file('abe/abe-questions.json')
  instructions = load_json_file('abe/abe-instructions.json')['instructions']

  # Run the synthetic poll and save the results
  output_file = synthetic_poll(agents, questions, instructions, data_folder)
  print(f"Responses saved to {output_file}")

  # Process saved data
  agents_data = load_json_file(output_file)
  generate_static_html_page(agents_data, base_folder, data_folder, pics_folder,
                            output_file)

  # Copy images to a local subfolder
  base_source_folder = 'agents/'
  copy_images_to_local(agents_data, base_source_folder, pics_folder)


main()
