
from flask import Flask, render_template, request, send_from_directory
import json
import os
import random

"""

FLASK SERVER REFERECING AGENTS.JSON 

"""

app = Flask(__name__)

# The path to the agents.json file
AGENTS_JSON_PATH = os.path.join('agents', 'agents.json')
# The base path for agent images
IMAGES_BASE_PATH = os.path.join('agents', 'pics')


@app.route('/')
def index():
  with open(AGENTS_JSON_PATH, 'r') as file:
    agents = json.load(file)
  for agent in agents:
    agent['photo_path'] = get_image_path(agent)
    if 'keywords' in agent and isinstance(agent['keywords'], list):
      agent['keywords'] = random.sample(agent['keywords'],
                                        min(len(agent['keywords']), 3))
    else:
      agent['keywords'] = []
  return render_template('index.html', agents=agents)


@app.route('/readme.html')
def readme():
    return render_template('readme.html')



def get_image_path(agent):
  # Retrieve the relative photo path from agent's data
  # The photo path is assumed to be in the format "pics/filename.png"
  return agent.get('photo_path', 'default.png')


@app.route('/agents/pics/<filename>')
def agent_pics(filename):
  return send_from_directory(IMAGES_BASE_PATH, filename)


if __name__ == '__main__':
  app.run(debug=True, host='0.0.0.0', port=81)
