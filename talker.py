#talker.py
from flask import Blueprint, render_template, request, jsonify, url_for, send_from_directory, abort, send_file
from models import Agent, User, Timeframe, Conversation, db
from flask_login import login_required, current_user
import openai
import os
import logging
from logging.handlers import RotatingFileHandler
import json
import datetime
import random

talker_blueprint = Blueprint('talker_blueprint', __name__, template_folder='templates')

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
  agent_type = None

  try:
    # Check if the agent exists in the User's agents_data
    user_agent_data = next((agent for agent in current_user.agents_data
                            if str(agent.get('id', '')) == str(agent_id)),
                           None)
    if user_agent_data:
      agent = Agent(id=user_agent_data['id'],
                    user_id=current_user.id,
                    data=user_agent_data)
      agent_type = 'agent'
      photo_path = agent.data.get('photo_path', '')
      photo_filename = photo_path.split('/')[-1]
      agent_image_data = current_user.images_data.get(photo_filename, '')

    # Check if the agent exists in the Agent model
    if not agent:
      agent = Agent.query.filter_by(user_id=current_user.id,
                                    id=str(agent_id)).first()
      if agent:
        agent_type = 'agent'
        photo_path = agent.data.get('photo_path', '')
        photo_filename = photo_path.split('/')[-1]
        agent_image_data = current_user.images_data.get(photo_filename, '')

    # Check if the agent exists in any of the user's timeframes
    if not agent:
      for timeframe in current_user.timeframes:
        timeframe_agents_data = json.loads(timeframe.agents_data)
        timeframe_agent_data = next(
            (agent for agent in timeframe_agents_data
             if str(agent.get('id', '')) == str(agent_id)), None)
        if timeframe_agent_data:
          agent = Agent(id=timeframe_agent_data['id'],
                        user_id=current_user.id,
                        data=timeframe_agent_data)
          agent_type = 'timeframe'
          photo_path = agent.data.get('photo_path', '')
          photo_filename = photo_path.split('/')[-1]
          agent_image_data = json.loads(summary_image_data).get(
              photo_filename, '')
          break

    if not agent:
      return "Agent not found", 404

    conversations = Conversation.query.filter(
        Conversation.user_id == current_user.id,
        Conversation.agents.cast(db.Text).contains(agent.id)).all()

    return render_template("talker.html",
                           agent_id=agent.id,
                           agent_jobtitle=agent.data.get('jobtitle', ''),
                           agent_summary=agent.data.get('summary', ''),
                           agent_image_data=agent_image_data,
                           agent_type=agent_type,
                           conversations=conversations)

  except Exception as e:
    logger.exception(f"Error in talker route: {str(e)}")
    return "An error occurred", 500


@talker_blueprint.route("/transcribe", methods=["POST"])
@login_required
def transcribe():
    logger.info(f"Transcribe route called with request files: {request.files}")

    if 'audio' not in request.files:
        logger.error("No audio file provided in the request")
        return jsonify({"error": "No audio file provided"}), 400

    audio_file = request.files['audio']
    logger.info(f"Received audio file: {audio_file}")

    assert audio_file.filename.endswith(('.mp3', '.wav')), "Audio file must be in MP3 or WAV format"

    user_folder = current_user.folder_path
    os.makedirs(user_folder, exist_ok=True)
    audio_file_path = os.path.join(user_folder, 'temp_audio.mp3')
    audio_file.save(audio_file_path)
    logger.info(f"Audio file saved to: {audio_file_path}")

    try:
        with open(audio_file_path, 'rb') as f:
            logger.info("Sending audio file to OpenAI for transcription")
            transcription = client.audio.transcriptions.create(model="whisper-1",
                                                               file=f,
                                                               language="en")
            logger.info(f"Received transcription: {transcription}")

        agent_id = request.form["agent_id"]
        logger.info(f"Agent ID: {agent_id}")

        agent = get_agent_by_id(agent_id, current_user)
        assert agent is not None, f"Agent not found for ID: {agent_id}"
        logger.info(f"Found agent: {agent}")

        conversation_id = request.form.get("conversation_id")
        conversation_name = request.form.get("conversation_name")
        logger.info(f"Conversation ID: {conversation_id}, Conversation Name: {conversation_name}")

        conversation_messages = []

        if conversation_id and conversation_id != 'undefined':
            try:
                conversation_id = int(conversation_id)
                conversation = Conversation.query.get(conversation_id)
                if conversation and conversation.user_id == current_user.id:
                    conversation_messages = conversation.messages
                    conversation_messages.append({"role": "user", "content": transcription.text})
                    db.session.commit()
                    logger.info(f"Appended user message to conversation {conversation_id}")
            except (ValueError, AssertionError) as e:
                logger.warning(f"Error processing conversation: {str(e)}")
                conversation_id = None

        if not conversation_id:
            conversation_id = 'temp'
            conversation_name = conversation_name or 'Temporary Conversation'
            conversation_messages.append({"role": "user", "content": transcription.text})
            logger.info("Using temporary conversation")

        response_text = chat_with_model(conversation_messages, agent.data, transcription.text)
        conversation_messages.append({"role": "assistant", "content": response_text})

        audio_url = text_to_speech(response_text, agent_id)

        return jsonify({
            "conversation_id": conversation_id,
            "conversation_name": conversation_name,
            "user_text": transcription.text,
            "ai_text": response_text,
            "audio_url": audio_url
        })

    except Exception as e:
        logger.exception(f"Error in transcription: {str(e)}")
        return jsonify({"error": str(e)}), 500

@talker_blueprint.route("/chat", methods=["POST"])
@login_required
def chat():
    user_message = request.form["user_message"]
    agent_id = request.form["agent_id"]
    conversation_id = request.form.get("conversation_id")
    conversation_name = request.form.get("conversation_name")

    agent = get_agent_by_id(agent_id, current_user)

    if not agent:
        return jsonify({"error": "Agent not found"}), 404

    if not conversation_id or conversation_id == 'null':
        conversation = Conversation(user_id=current_user.id,
                                    name=conversation_name,
                                    agents=[agent_id],
                                    messages=[])
        db.session.add(conversation)
        db.session.commit()
        conversation_id = conversation.id
    else:
        try:
            conversation_id = int(conversation_id)
            conversation = Conversation.query.get(conversation_id)
            if conversation and conversation.user_id == current_user.id:
                conversation.messages.append({"role": "user", "content": user_message})
                db.session.commit()
            else:
                return jsonify({"error": "Conversation not found"}), 404
        except ValueError:
            return jsonify({"error": "Invalid conversation ID"}), 400

    try:
        response_text = chat_with_model(conversation.messages, agent.data, user_message)
        conversation.messages.append({"role": "user", "content": user_message})
        conversation.messages.append({"role": "assistant", "content": response_text})
        db.session.commit()

        audio_url = text_to_speech(response_text, agent_id)

        return jsonify({
            "conversation_id": conversation_id,
            "conversation_name": conversation.name,
            "user_text": user_message,
            "ai_text": response_text,
            "audio_url": audio_url
        })
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        return jsonify({"error": str(e)}), 500


def chat_with_model(conversation_messages, agent_data, user_message, max_tokens=2000, top_p=0.5, temperature=0.9):
  logger.info(f"Entering chat_with_model for agent {agent_data['id']}")

  with open("abe/talker.json", "r") as f:
      prompts = json.load(f)

  gpt_system_prompt = prompts['gpt_system_prompt'].format(
      agent_id=agent_data['id'],
      agent_jobtitle=agent_data.get('jobtitle', ''),
      agent_summary=agent_data.get('summary', ''),
      agent_persona=agent_data.get('persona', ''),
      agent_relationships=agent_data.get('relationships', '')
  )

  messages = [{"role": "system", "content": gpt_system_prompt}]

  # Append the conversation history to the messages list with labels
  if conversation_messages:
      messages.append({"role": "system", "content": "Conversation History:"})
      for i, message in enumerate(conversation_messages, start=1):
          if message["role"] == "user":
              messages.append({"role": "system", "content": f"User Message {i}: {message['content']}"})
          else:
              messages.append({"role": "system", "content": f"AI Response {i}: {message['content']}"})
      messages.append({"role": "system", "content": "Current User Message:"})

  # Add the current user message to the messages list
  messages.append({"role": "user", "content": user_message})

  logger.info(f"Sending {len(messages)} messages to the model")
  logger.debug(f"System prompt: {gpt_system_prompt}")
  logger.debug(f"User prompt: {messages[-1]['content']}")


  try:
      response = client.chat.completions.create(
          model="gpt-4-turbo",
          messages=messages,
          max_tokens=max_tokens,
          top_p=top_p,
          temperature=temperature
      )

      logger.info("Model response received successfully")
      logger.debug(f"Model response: {response}")

      return response.choices[0].message.content

  except Exception as e:
      logger.exception(f"Error in chat_with_model: {str(e)}")
      return "Failed to generate response."

  finally:
      logger.info("Exiting chat_with_model")
  

@talker_blueprint.route('/audio/<path:filename>')
def serve_audio(filename):
  user_folder = current_user.folder_path
  file_path = os.path.join(user_folder, filename)
  if os.path.exists(file_path):
    return send_file(file_path, mimetype='audio/mpeg')
  else:
    abort(404)


def text_to_speech(text, agent_id):
  try:
      user_folder = current_user.folder_path
      os.makedirs(user_folder, exist_ok=True)
      timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
      file_path = os.path.join(user_folder, f'response_{timestamp}.mp3')

      agent = get_agent_by_id(agent_id, current_user)

      if agent:
          voice = agent.voice
      else:
          voice = 'echo'  # Default voice if agent not found

      with client.audio.speech.with_streaming_response.create(
          model="tts-1", voice=voice, input=text) as response:
          with open(file_path, 'wb') as audio_file:
              for chunk in response.iter_bytes():
                  audio_file.write(chunk)

      audio_url = url_for('talker_blueprint.serve_audio', filename=f'response_{timestamp}.mp3', _external=True)
      return audio_url
  except Exception as e:
      logger.error(f"Text-to-speech error: {str(e)}")
      return None


def truncate_messages(messages, max_chars):
  total_chars = sum(len(msg["content"]) for msg in messages)
  if total_chars <= max_chars:
    return messages

  truncated_messages = []
  remaining_chars = max_chars
  for msg in reversed(messages):
    if len(msg["content"]) <= remaining_chars:
      truncated_messages.insert(0, msg)
      remaining_chars -= len(msg["content"])
    else:
      break

  return truncated_messages



@talker_blueprint.route('/get_conversation_messages/<conversation_id>')
@login_required
def get_conversation_messages(conversation_id):
    try:
        # Convert conversation_id to int if not 'null', else handle the error or use a default.
        if conversation_id.lower() == 'null':
            return jsonify({'error': 'Invalid conversation ID'}), 400
        conversation_id = int(conversation_id)  # This will raise ValueError if conversion fails
        conversation = Conversation.query.get(conversation_id)
        if conversation and conversation.user_id == current_user.id:
            return jsonify({'messages': conversation.messages, 'name': conversation.name})
        else:
            return jsonify({'error': 'Conversation not found'}), 404
    except ValueError:
        return jsonify({'error': 'Invalid conversation ID'}), 400


@talker_blueprint.route('/update_conversation_name/<conversation_id>', methods=["POST"])
@login_required
def update_conversation_name(conversation_id):
    new_name = request.form.get("name")
    conversation = Conversation.query.get(conversation_id)
    if conversation and conversation.user_id == current_user.id:
        conversation.name = new_name
        db.session.commit()
        return jsonify({"success": True})
    else:
        return jsonify({"error": "Conversation not found"}), 404


def get_agent_by_id(agent_id, user):
    agent = Agent.query.filter_by(user_id=user.id, id=str(agent_id)).first()
    if agent:
        return agent
    
    user_agent_data = next((agent for agent in user.agents_data if str(agent.get('id', '')) == str(agent_id)), None)
    if user_agent_data:
        return Agent(id=user_agent_data['id'], user_id=user.id, data=user_agent_data, voice=user_agent_data.get('voice', 'echo'))
    
    for timeframe in user.timeframes:
        timeframe_agents_data = json.loads(timeframe.agents_data)
        timeframe_agent_data = next((agent for agent in timeframe_agents_data if str(agent.get('id', '')) == str(agent_id)), None)
        if timeframe_agent_data:
            return Agent(id=timeframe_agent_data['id'], user_id=user.id, data=timeframe_agent_data, voice=timeframe_agent_data.get('voice', 'echo'))
    
    return None