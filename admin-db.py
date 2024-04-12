#admin-db.py
import os
from abe import app, db
from models import User, Timeframe, Meeting


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

    timeframes = Timeframe.query.filter_by(user_id=user.id).all()
    log_lines.append(f"Number of Timeframes: {len(timeframes)}")

    for timeframe in timeframes:
      log_lines.append(f" Timeframe ID: {timeframe.id}")
      log_lines.append(f" Timeframe Name: {timeframe.name}")

      agents_with_image = 0
      agents_with_thumbnail = 0
      total_agents = len(timeframe.agents_data) if timeframe.agents_data else 0

      if timeframe.agents_data:
        for agent in timeframe.agents_data:
          photo_path = agent.get('photo_path', '')
          if photo_path:
            if user.images_data and photo_path in user.images_data:
              agents_with_image += 1
            if user.thumbnail_images_data and f"{photo_path}_thumbnail" in user.thumbnail_images_data:
              agents_with_thumbnail += 1

      log_lines.append(f" Number of Agents: {total_agents}")
      log_lines.append(f" Agents with Image: {agents_with_image}")
      log_lines.append(f" Agents with Thumbnail: {agents_with_thumbnail}")

    meetings = Meeting.query.filter_by(user_id=user.id).all()
    log_lines.append(f"Number of Meetings: {len(meetings)}")

    for meeting in meetings:
      log_lines.append(f" Meeting ID: {meeting.id}")
      log_lines.append(f" Meeting Name: {meeting.name}")
      log_lines.append(
          f" Number of Agents: {len(meeting.agents) if meeting.agents else 0}")
      log_lines.append(
          f" Number of Questions: {len(meeting.questions) if meeting.questions else 0}"
      )
      log_lines.append(
          f" Number of Answers: {len(meeting.answers) if meeting.answers else 0}"
      )

    log_lines.append(
        f"Number of Agents: {len(user.agents_data) if user.agents_data else 0}"
    )
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
    username = None  # Set the username to generate the log for a specific user, or leave it as None for all users
    generate_log(username)
