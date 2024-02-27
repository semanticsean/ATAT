#API_KEYS={"api_key1": "abcd1234efgh5678"}
#API_USAGE_LIMITS={"api_key1": 100}
#EMAIL_ADDRESS="your_email@example.com"
#EMAIL_PASSWORD="yourEmailPassword"
#SMTP_SERVER="smtp.example.com"
#SMTP_PORT=587
#OPENAI_API_KEY="openai_api_key_value"

from openai import OpenAI

client = OpenAI(api_key=OPENAI_API_KEY)
import os
import hashlib
import json
import html
import re
import smtplib

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends
from starlette.requests import Request
from starlette.responses import JSONResponse
from ratelimit import limits, RateLimitException
from ratelimit.auths import empty
from backoff import on_exception, expo
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

load_dotenv()  # Load environment variables

app = FastAPI()

# Load API keys and rate limiting info from environment variables
API_KEYS = json.loads(os.getenv("API_KEYS"))  # Assume format: {"key_name": "actual_key", ...}
API_USAGE_LIMITS = json.loads(os.getenv("API_USAGE_LIMITS"))  # Assume format: {"key_name": 100, ...}
EMAIL_CREDENTIALS = {
    "email": os.getenv("EMAIL_ADDRESS"),
    "password": os.getenv("EMAIL_PASSWORD"),
    "smtp_server": os.getenv("SMTP_SERVER"),
    "smtp_port": os.getenv("SMTP_PORT"),
}

# Load GPT-4 API configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

CALLS_PER_MINUTE = 2

def authenticate_api_key(api_key: str):
    """Check if the API key is valid and has usage left."""
    if api_key not in API_KEYS.values():
        raise HTTPException(status_code=401, detail="Invalid API key")

    # Hash the key name to match with the limits
    key_name = [name for name, key in API_KEYS.items() if key == api_key][0]
    hashed_key_name = hashlib.sha256(key_name.encode()).hexdigest()

    if API_USAGE_LIMITS.get(hashed_key_name, 0) <= 0:
        raise HTTPException(status_code=403, detail="API key usage exceeded")

    return api_key

@on_exception(expo, RateLimitException, max_tries=8)
@limits(calls=CALLS_PER_MINUTE, period=60)
async def rate_limit_check(request: Request, api_key: str = Depends(authenticate_api_key)):
    """Placeholder function to implement rate limiting."""
    return True

async def handle_request(request: Request, api_key: str = Depends(authenticate_api_key)):
    if not await rate_limit_check(request, api_key):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    request_data = await request.json()
    content = request_data.get("content", "")
    # Sanitize the input
    sanitized_content = html.escape(re.sub(r'[^\w\s]', '', content))

    # Load local JSON files
    with open('api-instructions.json', 'r') as f:
        api_instructions = json.load(f)
    with open('agents/agents.json', 'r') as f:
        agents = json.load(f)

    # Step 3: Make the GPT-4 call
    try:
        openai_response = client.completions.create(engine="text-davinci-003",
        prompt=f"{sanitized_content}\n\n{json.dumps(api_instructions)}",
        temperature=0.7,
        max_tokens=150,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0)
    except Exception as e:
        return JSONResponse(content={"error": "Failed to call OpenAI API"}, status_code=500)

    response_data = openai_response.get("choices", [{}])[0].get("text", "").strip()
    email_data = json.loads(response_data)

    # Validate the GPT-4 response
    agent_id = email_data.get("id")
    if agent_id not in [agent['id'] for agent in agents]:
        return JSONResponse(content={"error": "Invalid agent ID"}, status_code=400)

    # Step 4: Send Email
    try:
        send_email(email_data, EMAIL_CREDENTIALS)
    except Exception as e:
        return JSONResponse(content={"error": "Failed to send email"}, status_code=500)

    return JSONResponse(content={"message": "Request processed successfully"})

def send_email(email_data, email_credentials):
  msg = MIMEMultipart()
  msg['From'] = email_credentials['email']
  msg['To'] = email_data['email']
  msg['Subject'] = email_data.get('subject', 'No Subject')
  body = email_data.get('body', '')
  msg.attach(MIMEText(body, 'plain'))

  cc_list = email_data.get('cc_list', '').split(',')
  if len(cc_list) > 3:
      cc_list = cc_list[:3]  # Limit CC to 3 recipients
  msg['Cc'] = ','.join(cc_list)

  server = smtplib.SMTP(email_credentials['smtp_server'], email_credentials['smtp_port'])
  server.starttls()
  server.login(email_credentials['email'], email_credentials['password'])
  server.sendmail(email_credentials['email'], [email_data['email']] + cc_list, msg.as_string())
  server.quit()
