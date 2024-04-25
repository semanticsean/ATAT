from flask import Blueprint, render_template, request, jsonify, url_for, send_from_directory
from models import Agent, User, Timeframe
from flask_login import login_required, current_user
import openai
import os
import logging
from logging.handlers import RotatingFileHandler
import json

talker_blueprint = Blueprint('talker_blueprint',
                             __name__,
                             template_folder='templates')

handler = RotatingFileHandler('logs/talker.log', maxBytes=10000, backupCount=3)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(handler)

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@talker_blueprint.route("/talker/<agent_id>")
@login_required
def talker(agent_id):
    agent = None
    agent_image_data = None

    # Check if the agent exists in the User's agents_data
    user_agent_data = next((agent for agent in current_user.agents_data if str(agent.get('id', '')) == str(agent_id)), None)
    if user_agent_data:
        agent = Agent(id=user_agent_data['id'], user_id=current_user.id, data=user_agent_data)
        photo_path = agent.data.get('photo_path', '')  # Get the photo_path from agent.data
        photo_filename = photo_path.split('/')[-1]
        agent_image_data = current_user.images_data.get(photo_filename, '')

    # Check if the agent exists in the Agent model
    if not agent:
        agent = Agent.query.filter_by(user_id=current_user.id, id=str(agent_id)).first()
        if agent:
            photo_path = agent.data.get('photo_path', '')  # Get the photo_path from agent.data
            photo_filename = photo_path.split('/')[-1]
            agent_image_data = current_user.images_data.get(photo_filename, '')

    # Check if the agent exists in any of the user's timeframes
    if not agent:
        for timeframe in current_user.timeframes:
            timeframe_agents_data = json.loads(timeframe.agents_data)
            timeframe_agent_data = next((agent for agent in timeframe_agents_data if str(agent.get('id', '')) == str(agent_id)), None)
            if timeframe_agent_data:
                agent = Agent(id=timeframe_agent_data['id'], user_id=current_user.id, data=timeframe_agent_data)
                photo_path = agent.data.get('photo_path', '')  # Get the photo_path from agent.data
                photo_filename = photo_path.split('/')[-1]
                agent_image_data = json.loads(timeframe.images_data).get(photo_filename, '')
                break

    if not agent:
        return "Agent not found", 404

    return render_template("talker.html", agent=agent, agent_image_data=agent_image_data)


@talker_blueprint.route("/transcribe", methods=["POST"])
@login_required
def transcribe():
  if 'audio' not in request.files:
    logger.error("No audio file provided")
    return jsonify({"error": "No audio file provided"}), 400

  audio_file = request.files['audio']
  audio_file.save('temp_audio.mp3')

  try:
    with open('temp_audio.mp3', 'rb') as f:
      transcription = client.audio.transcriptions.create(model="whisper-1",
                                                         file=f,
                                                         language="en")
    logger.info("Transcription successful")

    agent_id = request.form["agent_id"]
    agent = Agent.query.filter_by(user_id=current_user.id, id=agent_id).first()
    if not agent:
      return jsonify({"error": "Agent not found"}), 404

    response_text = chat_with_model(transcription.text, agent)
    return jsonify({"user_text": transcription.text, "ai_text": response_text})
  except Exception as e:
    logger.error(f"Transcription error: {str(e)}")
    return jsonify({"error": str(e)}), 500


def chat_with_model(user_message,
                    agent,
                    max_tokens=1000,
                    top_p=0.5,
                    temperature=0.9):
  system_prompt = f"{agent.id} is {agent.jobtitle}. {agent.summary}\n\nPersona:\n{agent.persona}\n\nRelationships:\n{agent.relationships}"

  try:
    response = client.chat.completions.create(model="gpt-4",
                                              messages=[{
                                                  "role":
                                                  "system",
                                                  "content":
                                                  system_prompt
                                              }, {
                                                  "role": "user",
                                                  "content": user_message
                                              }],
                                              max_tokens=max_tokens,
                                              top_p=top_p,
                                              temperature=temperature)
    return response.choices[0].message.content
  except Exception as e:
    logger.error(f"Chat error: {str(e)}")
    return "Failed to generate response."


@talker_blueprint.route('/audio/<path:filename>')
def serve_audio(filename):
  return send_from_directory('static/audio', filename)


@talker_blueprint.route("/text-to-speech", methods=["POST"])
@login_required
def text_to_speech():
  text = request.form["text"]
  try:
    with client.audio.speech.with_streaming_response.create(
        model="tts-1", voice="nova", input=text) as response:
      file_path = os.path.join('static', 'audio', 'response.mp3')
      with open(file_path, 'wb') as audio_file:
        for chunk in response.iter_bytes():
          audio_file.write(chunk)
    audio_url = url_for('talker_blueprint.serve_audio',
                        filename='response.mp3')
    return jsonify({"audio_url": audio_url})
  except Exception as e:
    logger.error(f"Text-to-speech error: {str(e)}")
    return jsonify({"error": str(e)}), 500
