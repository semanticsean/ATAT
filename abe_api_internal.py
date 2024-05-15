# abe_api_internal.py

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from models import Meeting, User, Agent, Timeframe, Conversation, Survey, APIKey
from extensions import db
from pydantic import BaseModel
from fastapi.exceptions import HTTPException

from flask import jsonify

app = FastAPI()

class APIKeyHeader(BaseModel):
    Authorization: str

def get_db():
    db_session = db.session()
    try:
        yield db_session
    finally:
        db_session.close()

def verify_api_key(api_key_header: APIKeyHeader, db_session: Session = Depends(get_db)):
    api_key = api_key_header.Authorization.replace("Bearer ", "")
    user = db_session.query(User).join(APIKey).filter(APIKey.key == api_key).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return user

@app.get("/api/schema")
def get_schema(db_session: Session = Depends(get_db), user: User = Depends(verify_api_key)):
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
    return jsonify(schema)

@app.get("/api/agents")
def get_agents(db_session: Session = Depends(get_db), user: User = Depends(verify_api_key)):
    agents = db_session.query(Agent).filter(Agent.user_id == user.id).all()
    agent_data = []
    for agent in agents:
        agent_data.append({
            "id": agent.id,
            "data": agent.data,
            "agent_type": agent.agent_type,
            "voice": agent.voice
        })
    return jsonify(agent_data)

@app.get("/api/meetings")
def get_meetings(db_session: Session = Depends(get_db), user: User = Depends(verify_api_key)):
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
    return jsonify(meeting_data)

@app.get("/api/timeframes")
def get_timeframes(db_session: Session = Depends(get_db), user: User = Depends(verify_api_key)):
    timeframes = db_session.query(Timeframe).filter(Timeframe.user_id == user.id).all()
    timeframe_data = []
    for timeframe in timeframes:
        timeframe_data.append({
            "id": timeframe.id,
            "name": timeframe.name,
            "agents_data": timeframe.agents_data,
            "summary": timeframe.summary
        })
    return jsonify(timeframe_data)

@app.get("/api/conversations")
def get_conversations(db_session: Session = Depends(get_db), user: User = Depends(verify_api_key)):
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
    return jsonify(conversation_data)

@app.get("/api/surveys")
def get_surveys(db_session: Session = Depends(get_db), user: User = Depends(verify_api_key)):
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
    return jsonify(survey_data)


@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    # Log the exception details
    logger.error(f"An error occurred: {str(exc)}", exc_info=True)

    # Return a generic error response
    return JSONResponse(
        status_code=500,
        content={"message": "Internal Server Error"}
    )