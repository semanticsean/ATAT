# admin-db.py

import os
import sys
from abe import app, db
from models import User, Timeframe, Meeting
import json


def generate_log(username=None):
  log_lines = []

  if username:
    users = User.query.filter_by(username=username).all()
    log_lines.append(f"Generating log for user: {username}\n")
  else:
    users = User.query.all()
    log_lines.append("Generating log for all users\n")

  for user in users:
    log_lines.append(f"User ID: {user.id}")
    log_lines.append(f"Username: {user.username}")
    log_lines.append(f"Credits: {user.credits}")

    timeframe_ids = set()
    meeting_ids = set()

    log_lines.append(
        f"Number of Agents: {len(user.agents_data) if user.agents_data else 0}"
    )
    if user.agents_data:
      for agent in user.agents_data:
        log_lines.append(f"Agent ID: {agent['id']}")
        log_lines.append(f"Agent Name: {agent['id']}")
        log_lines.append(f"Agent Job Title: {agent.get('jobtitle', '')}")
        log_lines.append(f"Agent Image: {agent.get('photo_path', '')}")
        log_lines.append(
            f"Agent Relationships: {agent.get('relationships', [])}")
        log_lines.append(f"Agent Persona: {agent.get('persona', '')[:200]}")
        log_lines.append(f"Agent Summary: {agent.get('summary', '')[:200]}")
        log_lines.append(
            f"Agent Keywords: {', '.join(agent.get('keywords', []))}")
        log_lines.append(
            f"Agent Image Prompt: {agent.get('image_prompt', '')}")
        log_lines.append("")

    timeframes = Timeframe.query.filter_by(user_id=user.id).all()
    log_lines.append(f"Number of Timeframes: {len(timeframes)}")
    for timeframe in timeframes:
      if timeframe.id not in timeframe_ids:
        timeframe_ids.add(timeframe.id)
        agents_data = json.loads(
            timeframe.agents_data) if timeframe.agents_data else []
        log_lines.append(f"Timeframe ID: {timeframe.id}")
        log_lines.append(f"Timeframe Name: {timeframe.name}")
        log_lines.append(f"Number of Agents: {len(agents_data[:200])}")
        log_lines.append("")

    meetings = Meeting.query.filter_by(user_id=user.id).all()
    log_lines.append(f"Number of Meetings: {len(meetings)}")
    for meeting in meetings:
      if meeting.id not in meeting_ids:
        meeting_ids.add(meeting.id)
        log_lines.append(f"Meeting ID: {meeting.id}")
        log_lines.append(f"Meeting Name: {meeting.name}")
        log_lines.append(
            f"Number of Agents: {len(meeting.agents) if meeting.agents else 0}"
        )
        log_lines.append(
            f"Number of Questions: {len(meeting.questions) if meeting.questions else 0}"
        )
        log_lines.append(
            f"Number of Answers: {len(meeting.answers) if meeting.answers else 0}"
        )
        log_lines.append("")

    log_lines.append(
        f"Number of Images: {len(user.images_data) if user.images_data else 0}"
    )
    log_lines.append(
        f"Number of Thumbnails: {len(user.thumbnail_images_data) if user.thumbnail_images_data else 0}"
    )
    log_lines.append("\n")

  log_file_name = f"db_log{'_' + username if username else ''}.txt"
  with open(log_file_name, 'w') as log_file:
    log_file.write('\n'.join(log_lines))

  print(f"Log generated successfully: {log_file_name}")


if __name__ == '__main__':
  with app.app_context():
    username = sys.argv[1] if len(sys.argv) > 1 else None
    generate_log(username)
