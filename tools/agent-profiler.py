import json
import os
import time
import openai
from requests.exceptions import HTTPError


def read_json(file_path):
  with open(file_path, 'r') as file:
    return json.load(file)


def write_to_markdown(file_path, label, summary, tags, job_title):
  with open(file_path, 'a') as file:
    file.write(f"## {label}\n")
    if job_title:
      file.write(f"**Job Title:** {job_title}\n\n")
    file.write(f"{summary}\n\n")
    if tags:
      file.write(f"**Keywords:** {', '.join(tags)}\n\n")


def generate_summary(persona):
  try:
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{
            "role": "system",
            "content": "You are a helpful assistant."
        }, {
            "role":
            "user",
            "content":
            f"Generate a concise summary, a few keywords or tags, and the job title (if available) for this persona:\n\n{persona}"
        }],
        max_tokens=2000)
    return response.choices[0].message['content'].strip()
  except HTTPError as e:
    print(f"HTTP error occurred: {e}")
    # Implement exponential backoff here
    time.sleep(1)  # Placeholder for backoff logic
    return None


def extract_info(summary):
  lines = summary.split('\n')
  job_title = None
  tags = []

  for line in lines:
    if line.lower().startswith("job title:"):
      job_title = line.split(":", 1)[1].strip()
    elif line.lower().startswith("keywords:") or line.lower().startswith(
        "tags:"):
      tags = [tag.strip() for tag in line.split(":", 1)[1].split(",")]

  summary_text = "\n".join([
      line for line in lines
      if not line.lower().startswith(("job title:", "keywords:", "tags:"))
  ])
  return summary_text, tags, job_title


def main():
  openai.api_key = os.getenv('OPENAI_API_KEY')

  json_file_path = '../agents/agents.json'
  report_dir = 'reports'
  markdown_file_path = os.path.join(report_dir, 'persona_summaries.md')

  if not os.path.exists(report_dir):
    os.makedirs(report_dir)

  personas = read_json(json_file_path)

  for persona in personas:
    label = persona.get('id')
    description = persona.get('persona')
    if description:
      summary_response = generate_summary(description)
      if summary_response:
        summary, tags, job_title = extract_info(summary_response)
        write_to_markdown(markdown_file_path, label, summary, tags, job_title)


if __name__ == "__main__":
  main()
