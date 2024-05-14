import os
import sys
import json
import base64
from abe import app, db
from models import User, APIKey, Timeframe, Meeting, Agent, Image, MainAgent, Survey


def is_base64(sb):
  """Check if the input is base64 encoded."""
  try:
    if isinstance(sb, str):
      sb_bytes = bytes(sb, 'ascii')
    elif isinstance(sb, bytes):
      sb_bytes = sb
    else:
      raise ValueError("Argument must be string or bytes")
    return base64.b64encode(base64.b64decode(sb_bytes)) == sb_bytes
  except Exception:
    return False


def format_data(data, max_length=50):
  """Format data for logging, handling base64 and truncating as necessary."""
  data_str = json.dumps(data) if isinstance(data, (dict, list)) else str(data)
  if is_base64(data_str):
    return "image in base64"
  if len(data_str) > max_length:
    return data_str[:max_length - 3] + '...'
  return data_str


def generate_log(username=None):
  log_lines = []
  user_query = User.query.filter_by(
      username=username) if username else User.query.all()

  for user in user_query:
    user_details = [
        f"User ID: {user.id}", f"Username: {format_data(user.username)}",
        f"Email: {format_data(user.email)}",
        f"Password Hash: {format_data(user.password_hash)}",
        f"Credits: {format_data(user.credits)}",
        f"Agents Data: {format_data(json.dumps(user.agents_data))}",
        f"Images Data: {format_data(json.dumps(user.images_data))}",
        f"Thumbnail Images Data: {format_data(json.dumps(user.thumbnail_images_data))}"
    ]
    log_lines.extend(user_details)

    api_keys = [
        f"API Key: {format_data(key.key)}" for key in user.api_keys.all()
    ]
    log_lines.append(f"API Keys: {'✅' if api_keys else '❌'}")
    log_lines.extend(api_keys)

    agents = user.agents
    log_lines.append(f"Agents: {'✅' if agents else '❌'}")
    for agent in agents:
      agent_info = [
          f"Agent ID: {agent.id}", f"Agent Type: {agent.agent_type}",
          f"Persona: {format_data(agent.persona)}",
          f"Summary: {format_data(agent.summary)}",
          f"Keywords: {format_data(', '.join(agent.keywords))}",
          f"Image Prompt: {format_data(agent.image_prompt)}",
          f"Relationships: {format_data(', '.join(map(json.dumps, agent.relationships)))}"
      ]
      if agent.data and 'photo_path' in agent.data:
        agent_info.append(
            f"Photo Path: {format_data(agent.data['photo_path'])}")
      if agent.data and 'image_data' in agent.data:
        agent_info.append(
            f"Image Data: {'✅' if agent.data['image_data'] else '❌'}")
      log_lines.extend(agent_info)

    images = user.images
    log_lines.append(f"Images: {'✅' if images else '❌'}")
    for image in images:
      image_info = [
          f"Image ID: {image.id}", f"Filename: {format_data(image.filename)}"
      ]
      log_lines.extend(image_info)

    main_agents = user.main_agents
    log_lines.append(f"Main Agents: {'✅' if main_agents else '❌'}")
    for main_agent in main_agents:
      main_agent_info = [
          f"Main Agent ID: {main_agent.id}",
          f"Data: {format_data(main_agent.data)}",
          f"Image Data: {format_data(main_agent.image_data[:12])}"
      ]
      log_lines.extend(main_agent_info)

    surveys = user.surveys
    log_lines.append(f"Surveys: {'✅' if surveys else '❌'}")
    for survey in surveys:
      survey_info = [
          f"Survey ID: {survey.id}", f"Name: {format_data(survey.name)}",
          f"Data: {format_data(json.dumps(survey.survey_data))}",
          f"Is Public: {'✅' if survey.is_public else '❌'}",
          f"Public URL: {format_data(survey.public_url)}"
      ]
      log_lines.extend(survey_info)

    timeframes = user.timeframes
    log_lines.append(f"Timeframes: {'✅' if timeframes else '❌'}")
    for timeframe in timeframes:
      timeframe_info = [
          f"Timeframe ID: {timeframe.id}",
          f"Name: {format_data(timeframe.name)}",
          f"Agents Count: {format_data(timeframe.agents_count)}",
          f"Images Data: {format_data(timeframe.summary_image_data)}",
          f"Thumbnail Images Data: {format_data(timeframe.thumbnail_images_data)}"
      ]
      log_lines.extend(timeframe_info)

    meetings = user.meetings
    log_lines.append(f"Meetings: {'✅' if meetings else '❌'}")
    for meeting in meetings:
      meeting_info = [
          f"Meeting ID: {meeting.id}", f"Name: {format_data(meeting.name)}",
          f"Agents: {format_data(json.dumps(meeting.agents))}",
          f"Questions: {format_data(json.dumps(meeting.questions))}",
          f"Answers: {format_data(json.dumps(meeting.answers))}",
          f"Is Public: {'✅' if meeting.is_public else '❌'}",
          f"Public URL: {format_data(meeting.public_url)}"
      ]
      log_lines.extend(meeting_info)

    log_lines.append("\n")

  log_file_name = f"db_log{'_' + username if username else ''}.txt"
  with open(log_file_name, 'w') as log_file:
    log_file.write('\n'.join(log_lines))

  print(f"Log generated successfully: {log_file_name}")


if __name__ == '__main__':
  with app.app_context():
    username = sys.argv[1] if len(sys.argv) > 1 else None
    generate_log(username)
