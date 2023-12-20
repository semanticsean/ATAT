import json
import re
from datetime import datetime
import uuid


def parse_markdown(file_path):
  with open(file_path, 'r', encoding='utf-8') as file:
    lines = file.readlines()

  personas = []
  current_persona = {}
  collecting = False
  unique_id_counter = 1

  for line in lines:
    if line.startswith('## '):
      if current_persona:
        personas.append(current_persona)
        current_persona = {}
      name = line.strip('# ').strip()
      current_persona['name'] = name
      current_persona[
          'photo_path'] = f"/agent-profile/pics/{name.replace(' ', '').lower()}.png"
      current_persona['unique_id'] = str(
          uuid.uuid4())  # or use f"agent_{unique_id_counter}"
      current_persona['timestamp'] = datetime.now().isoformat()
      unique_id_counter += 1
      collecting = True
    elif collecting:
      if line.strip().startswith('**Job Title:**'):
        current_persona['job_title'] = line.strip().split(
            '**Job Title:**')[1].strip()
      elif 'Job title' in line and 'job_title' not in current_persona:
        job_title_match = re.search(r'Job title \(if available\): (.*)', line)
        if job_title_match:  # Check if there's a match
          current_persona['job_title'] = job_title_match.group(1)
      elif line.strip().startswith('Summary:'):
        current_persona['summary'] = line.strip().split('Summary:')[1].strip()
      elif line.strip().startswith(
          'Keywords/Tags:') or line.strip().startswith('**Keywords:**'):
        current_persona['keywords'] = line.strip().split(
            ':', 1)[1].strip().split(', ')

  if current_persona:  # Add the last persona
    personas.append(current_persona)

  return personas


def save_to_json(personas, output_file):
  with open(output_file, 'w', encoding='utf-8') as file:
    json.dump(personas, file, indent=4, ensure_ascii=False)


# Example usage
file_path = 'reports/persona_summaries.md'
output_file = 'personas.json'
personas = parse_markdown(file_path)
save_to_json(personas, output_file)
