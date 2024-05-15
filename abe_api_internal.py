# abe_api_internal.py

from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from models import Meeting, User, Agent, Timeframe, Conversation, Survey, APIKey
from extensions import db
from pydantic import BaseModel
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
import traceback
import logging

logger = logging.getLogger(__name__)

app = FastAPI()

class APIKeyHeader(BaseModel):
    Authorization: str

def get_db_session():
    db_session = db.session()
    try:
        yield db_session
    finally:
        db_session.close()

def verify_api_key(api_key_header: APIKeyHeader, db_session: Session = Depends(get_db_session)):
    api_key = api_key_header.Authorization.replace("Bearer ", "")
    user = db_session.query(User).join(APIKey).filter(APIKey.key == api_key).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return user

@app.get("/api/schema")
def get_schema(user: User = Depends(verify_api_key), db_session: Session = Depends(get_db_session)):
    schema = {
        "agents": {
            "count": db_session.query(Agent).filter(Agent.user_id == user.id).count(),
            "endpoint": "/api/agents"
        },
        "meetings": {
            "count": db_session.query(Meeting).filter(Meeting.user_id == user.id).count(),
            "endpoint": "/api/meetings"
        },
        "timeframes": {
            "count": db_session.query(Timeframe).filter(Timeframe.user_id == user.id).count(),
            "endpoint": "/api/timeframes"
        },
        "conversations": {
            "count": db_session.query(Conversation).filter(Conversation.user_id == user.id).count(),
            "endpoint": "/api/conversations"
        },
        "surveys": {
            "count": db_session.query(Survey).filter(Survey.user_id == user.id).count(),
            "endpoint": "/api/surveys"
        }
    }
    return schema

@app.get("/api/agents")
def get_agents(user: User = Depends(verify_api_key), db_session: Session = Depends(get_db_session)):

    agents = db_session.query(Agent).filter(Agent.user_id == user.id).all()
    agent_data = []
    for agent in agents:
        agent_data.append({
            "id": agent.id,
            "data": agent.data,
            "agent_type": agent.agent_type,
            "voice": agent.voice
        })
    return agent_data

@app.get("/api/meetings")
def get_meetings(user: User = Depends(verify_api_key), db_session: Session = Depends(get_db_session)):
    meetings = db_session.query(Meeting).filter(Meeting.user_id == user.id).all()
    meeting_data = []
    for meeting in meetings:
        meeting_data.append({
            "id": meeting.id,
            "name": meeting.name,
            "agents": meeting.agents,
            "questions": meeting.questions,
            "answers": meeting.answers,
            "is_public": meeting.is_public,
            "public_url": meeting.public_url
        })
    return meeting_data

@app.get("/api/timeframes")
def get_timeframes(user: User = Depends(verify_api_key), db_session: Session = Depends(get_db_session)):
    timeframes = db_session.query(Timeframe).filter(Timeframe.user_id == user.id).all()
    timeframe_data = []
    for timeframe in timeframes:
        timeframe_data.append({
            "id": timeframe.id,
            "name": timeframe.name,
            "agents_data": timeframe.agents_data,
            "summary": timeframe.summary
        })
    return timeframe_data

@app.get("/api/conversations")
def get_conversations(user: User = Depends(verify_api_key), db_session: Session = Depends(get_db_session)):
    conversations = db_session.query(Conversation).filter(Conversation.user_id == user.id).all()
    conversation_data = []
    for conversation in conversations:
        conversation_data.append({
            "id": conversation.id,
            "name": conversation.name,
            "agents": conversation.agents,
            "messages": conversation.messages,
            "timestamp": conversation.timestamp.isoformat(),
            "url": conversation.url
        })
    return conversation_data

@app.get("/api/surveys")
def get_surveys(user: User = Depends(verify_api_key), db_session: Session = Depends(get_db_session)):
    surveys = db_session.query(Survey).filter(Survey.user_id == user.id).all()
    survey_data = []
    for survey in surveys:
        survey_data.append({
            "id": survey.id,
            "name": survey.name,
            "survey_data": survey.survey_data,
            "is_public": survey.is_public,
            "public_url": survey.public_url
        })
    return survey_data

@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    # Log the exception details
    logger.error(f"An error occurred: {str(exc)}", exc_info=True)

    # Check if the API key is valid
    api_key_header = APIKeyHeader(Authorization=request.headers.get("Authorization", ""))
    try:
        db_session = next(get_db_session())
        user = verify_api_key(api_key_header, db_session)
        # If the API key is valid, show the error details to the API request maker
        return JSONResponse(
            status_code=500,
            content={
                "message": "Internal Server Error",
                "error": str(exc),
                "traceback": traceback.format_exc()
            }
        )
    except HTTPException as e:
        if e.status_code == 401:
            # If the API key is invalid, return a generic error response
            return JSONResponse(
                status_code=500,
                content={"message": "Internal Server Error"}
            )
        else:
            raise e