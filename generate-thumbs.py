#generate_thumbs.py
"""
This script does the following:

The generate_thumbnails function takes an optional user_id parameter. If user_id is provided, it generates thumbnails for that specific user. Otherwise, it generates thumbnails for all users in the database.
It iterates over each user's images_data, agents, and timeframes to generate thumbnails for all possible image types.
For images_data, it generates thumbnails and appends them to the user's thumbnail_images_data dictionary with the key format {filename}_thumbnail.
For agents, it checks if the agent has image_data and generates a thumbnail, storing it in the agent's data as thumbnail_image_data.
For timeframes, it loads the images_data from the JSON string, generates thumbnails for each image, and appends them to the timeframe's thumbnail_images_data dictionary.
It keeps a log of all the added thumbnails in a file named added_thumbnails.log. The log format is (user_id, record_type, thumbnail_key) for user and agent records, and (user_id, record_type, timeframe_id, thumbnail_key) for timeframe records.
The rollback_thumbnails function reads the added_thumbnails.log file and removes the thumbnails that were added by the script. It pops the thumbnail keys from the respective user, agent, or timeframe data.
The generate_thumbnail function takes the image_data as input, resizes it to a thumbnail size of (200, 200) using the PIL library, and returns the thumbnail data as a base64-encoded string.

To use this script, you can run it with python thumbnail_generator.py (assuming the script is named thumbnail_generator.py). It will generate thumbnails for all users by default. You can uncomment the generate_thumbnails(user_id=1) line to generate thumbnails for a specific user (replace 1 with the desired user ID). To rollback the added thumbnails, you can uncomment the rollback_thumbnails() line.
Note: Make sure to have the necessary dependencies (PIL library) installed and adjust the import statements based on your project structure.

"""
#generate_thumbs.py
import os
import base64
import json
from io import BytesIO
from PIL import Image
from abe import app, db
from models import User, Agent, Timeframe


def generate_thumbnails(user_id=None):
  if user_id:
      users = User.query.filter_by(id=user_id).all()
  else:
      users = User.query.all()

  added_thumbnails = []

  for user in users:
      print(f"Processing user: {user.id}")

      # Generate thumbnails for user's images_data
      if user.images_data:
          for filename, image_data in user.images_data.items():
              print(f"Generating thumbnail for user {user.id}, image: {filename}")
              thumbnail_data = generate_thumbnail(image_data)
              thumbnail_key = f"{filename}_thumbnail"
              user.thumbnail_images_data[thumbnail_key] = thumbnail_data
              added_thumbnails.append((user.id, 'user', thumbnail_key))
      else:
          print(f"No images_data found for user: {user.id}")

      # Generate thumbnails for user's agents
      for agent in user.agents:
          if 'photo_path' in agent.data:
              photo_filename = agent.data['photo_path'].split('/')[-1]
              image_data = user.images_data.get(photo_filename) if user.images_data else None
              if image_data:
                  print(f"Generating thumbnail for user {user.id}, agent: {agent.id}")
                  thumbnail_data = generate_thumbnail(image_data)
                  agent.data['thumbnail_image_data'] = thumbnail_data
                  added_thumbnails.append((user.id, 'agent', agent.id))
              else:
                  print(f"No image data found for user {user.id}, agent: {agent.id}")
          else:
              print(f"No photo_path found for user {user.id}, agent: {agent.id}")

      # Generate thumbnails for user's timeframes
      for timeframe in user.timeframes:
          images_data = json.loads(timeframe.summary_image_data) if timeframe.timeframe else {}
          for filename, image_data in images_data.items():
              print(f"Generating thumbnail for user {user.id}, timeframe: {timeframe.id}, image: {filename}")
              thumbnail_data = generate_thumbnail(image_data)
              thumbnail_key = f"{filename}_thumbnail"
              timeframe_thumbnail_images_data = json.loads(timeframe.thumbnail_images_data) if timeframe.thumbnail_images_data else {}
              timeframe_thumbnail_images_data[thumbnail_key] = thumbnail_data
              timeframe.thumbnail_images_data = json.dumps(timeframe_thumbnail_images_data)
              added_thumbnails.append((user.id, 'timeframe', timeframe.id, thumbnail_key))

  db.session.commit()

  # Save the log of added thumbnails
  with open('added_thumbnails.log', 'w') as log_file:
      for thumbnail in added_thumbnails:
          log_file.write(f"{thumbnail}\n")


def rollback_thumbnails():
  try:
    with open('added_thumbnails.log', 'r') as log_file:
      for line in log_file:
        thumbnail = eval(line.strip())
        if len(thumbnail) == 3:
          user_id, record_type, thumbnail_key = thumbnail
          if record_type == 'user':
            user = User.query.get(user_id)
            user.thumbnail_images_data.pop(thumbnail_key, None)
          elif record_type == 'agent':
            agent = Agent.query.get(thumbnail_key)
            agent.data.pop('thumbnail_image_data', None)
        elif len(thumbnail) == 4:
          user_id, record_type, timeframe_id, thumbnail_key = thumbnail
          if record_type == 'timeframe':
            timeframe = Timeframe.query.get(timeframe_id)
            timeframe_thumbnail_images_data = json.loads(
                timeframe.thumbnail_images_data)
            timeframe_thumbnail_images_data.pop(thumbnail_key, None)
            timeframe.thumbnail_images_data = json.dumps(
                timeframe_thumbnail_images_data)

    db.session.commit()
    os.remove('added_thumbnails.log')
    print("Thumbnails rolled back successfully.")
  except FileNotFoundError:
    print("No thumbnail log file found. Rollback not required.")


def generate_thumbnail(image_data):
  thumbnail_size = (200, 200)
  img = Image.open(BytesIO(base64.b64decode(image_data)))
  img.thumbnail(thumbnail_size)
  thumbnail_buffer = BytesIO()
  img.save(thumbnail_buffer, format='PNG')
  thumbnail_data = base64.b64encode(
      thumbnail_buffer.getvalue()).decode('utf-8')
  return thumbnail_data


if __name__ == '__main__':
  with app.app_context():
    generate_thumbnails()  # Generate thumbnails for all users
    # generate_thumbnails(user_id=1)  # Generate thumbnails for a specific user
    # rollback_thumbnails()  # Rollback the added thumbnails
