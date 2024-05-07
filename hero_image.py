#hero_image.py 
import os
import json
import base64
import requests
from models import db, User
from openai import OpenAI
import logging
import traceback


client = OpenAI()
openai_api_key = os.environ['OPENAI_API_KEY']

def generate_hero_image(current_user):
    try:
        logging.info(f"Generating hero image for user: {current_user.id}")
        agents = current_user.agents_data + [agent.data for agent in current_user.agents]
    
        agent_data = []
        for agent in agents:
            agent_data.append({
                'id': agent['id'],
                'jobtitle': agent['jobtitle'],
                'persona': agent.get('persona', '')[:1000]  # Use get() method with a default value
            })
    
        gpt4_prompt = f"Please generate a DALL-E image description prompt for a group photo featuring the following characters:\n\n{json.dumps(agent_data, indent=2)}\n\nEnsure that ALL participants are included as individual characters in the group photo."
    
        gpt4_payload = {
            "model": "gpt-4-turbo",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant that generates DALL-E image description prompts."},
                {"role": "user", "content": gpt4_prompt}
            ]
        }
    
        logging.info(f"Sending request to OpenAI GPT-4 API with payload: {gpt4_payload}")
        gpt4_response = client.chat.completions.create(**gpt4_payload)
    
        if gpt4_response.status_code != 200:
            error_message = f"OpenAI GPT-4 API returned an error: {gpt4_response.text}"
            logging.error(error_message)
            raise Exception(error_message)
    
        dalle_prompt = gpt4_response.choices[0].message.content.strip()
        logging.info(f"Received DALL-E prompt from GPT-4: {dalle_prompt}")
    
        dalle_payload = {
            "model": "dall-e-3",
            "prompt": f"{dalle_prompt}\n\nNote: ALL characters mentioned must be displayed in the photo.",
            "quality": "standard",
            "size": "1024x1024",
            "n": 1
        }
    
        logging.info(f"Sending request to OpenAI DALL-E API with payload: {dalle_payload}")
        dalle_response = client.images.generate(**dalle_payload)
    
        if dalle_response.status_code != 200:
            error_message = f"OpenAI DALL-E API returned an error: {dalle_response.text}"
            logging.error(error_message)
            raise Exception(error_message)
    
        image_url = dalle_response.data[0].url
        logging.info(f"Received image URL from DALL-E: {image_url}")
    
        img_data = requests.get(image_url).content
        encoded_string = base64.b64encode(img_data).decode('utf-8')
        current_user.images_data['hero_image'] = encoded_string
        db.session.commit()
    
        logging.info(f"Hero image generated and stored successfully for user: {current_user.id}")
        return encoded_string
    
    except Exception as e:
        logging.error(f"Error generating hero image for user: {current_user.id}")
        logging.error(f"Exception: {str(e)}")
        logging.error(traceback.format_exc())
        # Return an empty string or a default image
        return ""