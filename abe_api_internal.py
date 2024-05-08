#abe_api_internal.py 

import asyncio
import json
import logging
import os
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import BackgroundTasks, FastAPI
from pydantic import BaseModel

from abe_gpt import conduct_meeting, generate_new_agent, process_agents

app = FastAPI()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')


class AgentRequest(BaseModel):
    agent_id: Optional[str] = None
    agent_name: Optional[str] = None
    jobtitle: Optional[str] = None
    agent_description: Optional[str] = None


class TimeframeRequest(BaseModel):
    agents_data: List[AgentRequest]
    instructions: dict
    timeframe_name: Optional[str] = None


class MeetingRequest(BaseModel):
    agents_data: List[AgentRequest]
    questions: dict
    meeting_id: str
    meeting_name: Optional[str] = None
    llm_instructions: Optional[str] = None
    request_type: str


class APIRequest(BaseModel):
    request_id: str = str(uuid.uuid4())
    request_type: str
    priority: bool = False
    agent_request: Optional[AgentRequest] = None
    timeframe_request: Optional[TimeframeRequest] = None
    meeting_request: Optional[MeetingRequest] = None


request_queue = asyncio.Queue()
completed_requests = []


async def process_request_queue(current_user):
    while True:
        request = await request_queue.get()
        try:
            if request.request_type == "new_agent":
                new_agent = generate_new_agent(
                    agent_name=request.agent_request.agent_name,
                    jobtitle=request.agent_request.jobtitle,
                    agent_description=request.agent_request.agent_description,
                    current_user=current_user
                )
                result = new_agent.id
  
            elif request.request_type == "process_agents":
                new_timeframe = process_agents(
                    payload={
                        "agents_data": [agent.dict() for agent in request.timeframe_request.agents_data],
                        "instructions": request.timeframe_request.instructions,
                        "timeframe_name": request.timeframe_request.timeframe_name or f"Timeframe {uuid.uuid4()}"
                    },
                    current_user=current_user
                )
                result = new_timeframe.id
  
            elif request.request_type == "conduct_meeting":
                meeting_responses = conduct_meeting(
                    payload={
                        "agents_data": [agent.dict() for agent in request.meeting_request.agents_data],
                        "questions": request.meeting_request.questions,
                        "meeting_id": request.meeting_request.meeting_id,
                        "meeting_name": request.meeting_request.meeting_name or f"Meeting {uuid.uuid4()}",
                        "llm_instructions": request.meeting_request.llm_instructions,
                        "request_type": request.meeting_request.request_type
                    },
                    current_user=current_user
                )
                result = meeting_responses
  
            else:
                raise ValueError(f"Invalid request type: {request.request_type}")
  
            logging.info(f"Processed request {request.request_id}")
            return result
  
        except Exception as e:
            logging.error(f"Error processing request {request.request_id}: {e}")
  
        finally:
            request_queue.task_done()

@app.post("/api/request")
async def create_request(api_request: APIRequest, background_tasks: BackgroundTasks, current_user=None):
    if api_request.priority:
        await request_queue.put(api_request)
    else:
        background_tasks.add_task(request_queue.put, api_request)

    return {"message": "Request added to the queue", "request_id": api_request.request_id}


@app.get("/api/request/{request_id}")
async def get_request_status(request_id: str):
    for request in completed_requests:
        if request["request_id"] == request_id:
            return {"status": "completed", "result": request["result"]}

    return {"status": "pending"}


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(process_request_queue(current_user=None))  # Pass the current user object here