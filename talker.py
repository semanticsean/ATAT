#talker.py
from flask import Blueprint, render_template, request, jsonify, url_for, send_from_directory, abort, send_file
from models import Agent, User, Timeframe
from flask_login import login_required, current_user
import openai
import os
import logging
from logging.handlers import RotatingFileHandler
import json
import datetime

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

    try:
        # Check if the agent exists in the User's agents_data
        user_agent_data = next((agent for agent in current_user.agents_data if str(agent.get('id', '')) == str(agent_id)), None)
        if user_agent_data:
            agent = Agent(id=user_agent_data['id'], user_id=current_user.id, data=user_agent_data)
            photo_path = agent.data.get('photo_path', '')
            photo_filename = photo_path.split('/')[-1]
            agent_image_data = current_user.images_data.get(photo_filename, '')
            logger.debug(f"Agent found in user's agents_data: {agent}")

        # Check if the agent exists in the Agent model
        if not agent:
            agent = Agent.query.filter_by(user_id=current_user.id, id=str(agent_id)).first()
            if agent:
                photo_path = agent.data.get('photo_path', '')
                photo_filename = photo_path.split('/')[-1]
                agent_image_data = current_user.images_data.get(photo_filename, '')
                logger.debug(f"Agent found in Agent model: {agent}")

        # Check if the agent exists in any of the user's timeframes
        if not agent:
            for timeframe in current_user.timeframes:
                timeframe_agents_data = json.loads(timeframe.agents_data)
                timeframe_agent_data = next((agent for agent in timeframe_agents_data if str(agent.get('id', '')) == str(agent_id)), None)
                if timeframe_agent_data:
                    agent = Agent(id=timeframe_agent_data['id'], user_id=current_user.id, data=timeframe_agent_data)
                    photo_path = agent.data.get('photo_path', '')
                    photo_filename = photo_path.split('/')[-1]
                    agent_image_data = json.loads(timeframe.images_data).get(photo_filename, '')
                    logger.debug(f"Agent found in timeframe: {timeframe}")
                    break

        if not agent:
            logger.warning(f"Agent not found for ID: {agent_id}")
            return "Agent not found", 404

        logger.info(f"Rendering talker.html for agent: {agent}")
        return render_template("talker.html",
                               agent_id=agent.id,
                               agent_jobtitle=agent.data.get('jobtitle', ''),
                               agent_summary=agent.data.get('summary', ''),
                               agent_image_data=agent_image_data,
                               agent_type='agent')  # Add this line

    except Exception as e:
        logger.exception(f"Error in talker route: {str(e)}")
        return "An error occurred", 500


@talker_blueprint.route("/transcribe", methods=["POST"])
@login_required
def transcribe():
    if 'audio' not in request.files:
        logger.error("No audio file provided")
        return jsonify({"error": "No audio file provided"}), 400

    audio_file = request.files['audio']
    user_folder = current_user.folder_path
    os.makedirs(user_folder, exist_ok=True)
    audio_file_path = os.path.join(user_folder, 'temp_audio.mp3')
    audio_file.save(audio_file_path)
    logger.info(f"Audio file saved at: {audio_file_path}")

    try:
        with open(audio_file_path, 'rb') as f:
            transcription = client.audio.transcriptions.create(model="whisper-1",
                                                               file=f,
                                                               language="en")
        logger.info("Transcription successful")
        logger.info(f"Transcription result: {transcription.text}")

        agent_id = request.form["agent_id"]
        agent = None

        # Check if the agent exists in the User's agents_data
        user_agent_data = next((agent for agent in current_user.agents_data if str(agent.get('id', '')) == str(agent_id)), None)
        if user_agent_data:
            agent = Agent(id=user_agent_data['id'], user_id=current_user.id, data=user_agent_data)
            logger.debug(f"Agent found in user's agents_data: {agent}")

        # Check if the agent exists in the Agent model
        if not agent:
            agent = Agent.query.filter_by(user_id=current_user.id, id=str(agent_id)).first()
            if agent:
                logger.debug(f"Agent found in Agent model: {agent}")

        # Check if the agent exists in any of the user's timeframes
        if not agent:
            for timeframe in current_user.timeframes:
                timeframe_agents_data = json.loads(timeframe.agents_data)
                timeframe_agent_data = next((agent for agent in timeframe_agents_data if str(agent.get('id', '')) == str(agent_id)), None)
                if timeframe_agent_data:
                    agent = Agent(id=timeframe_agent_data['id'], user_id=current_user.id, data=timeframe_agent_data)
                    logger.debug(f"Agent found in timeframe: {timeframe}")
                    break

        if not agent:
            logger.error(f"Agent not found for ID: {agent_id}")
            return jsonify({"error": "Agent not found"}), 404

        response_text = chat_with_model(transcription.text, agent)
        logger.info(f"Generated response: {response_text}")

        response_data = {"user_text": transcription.text, "ai_text": response_text}
        logger.info(f"Response data: {response_data}")

        # Generate audio response
        audio_file_path = text_to_speech_sync(response_text, agent)
        if audio_file_path:
            response_data["audio_file_path"] = audio_file_path
        else:
            logger.warning("Failed to generate audio response")
            response_data["audio_file_path"] = None  # Add this line
  
        return jsonify(response_data)

    except Exception as e:
        logger.error(f"Transcription error: {str(e)}")
        return jsonify({"error": str(e)}), 500


def chat_with_model(user_message,
                    agent,
                    max_tokens=250,
                    top_p=0.5,
                    temperature=0.9):
  with open("abe/talker.json", "r") as f:
    prompts = json.load(f)

  gpt_system_prompt = prompts['gpt_system_prompt'].format(
      agent_id=agent.id,
      agent_jobtitle=agent.data.get('jobtitle', ''),
      agent_summary=agent.data.get('summary', ''),
      agent_persona=agent.data.get('persona', ''),
      agent_relationships=agent.data.get('relationships', ''))

  try:
    response = client.chat.completions.create(model="gpt-4-turbo",
                                              messages=[{
                                                  "role":
                                                  "system",
                                                  "content":
                                                  gpt_system_prompt
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
  user_folder = current_user.folder_path
  file_path = os.path.join(user_folder, filename)
  if os.path.exists(file_path):
    return send_file(file_path, mimetype='audio/mpeg')
  else:
    abort(404)


def text_to_speech_sync(text, agent):
  try:
      user_folder = current_user.folder_path
      os.makedirs(user_folder, exist_ok=True)
      timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
      audio_file_path = os.path.join(user_folder, f'response_{timestamp}.mp3')

      with client.audio.speech.with_streaming_response.create(
          model="tts-1", voice="nova", input=text) as response:
          with open(audio_file_path, 'wb') as audio_file:
              for chunk in response.iter_bytes():
                  audio_file.write(chunk)
      logger.info(f"Generated audio file saved at: {audio_file_path}")
      return audio_file_path
  except Exception as e:
      logger.error(f"Text-to-speech error: {str(e)}")
      return None