import sys
import os

# Disable mTLS client certificates to avoid pyOpenSSL context crashes on Google Linux workstations
os.environ["GOOGLE_API_USE_CLIENT_CERTIFICATE"] = "false"
os.environ["GOOGLE_API_USE_MTLS"] = "never"
sys.modules['OpenSSL'] = None
sys.modules['urllib3.contrib.pyopenssl'] = None

import uuid
import logging
import datetime
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables from parent directory .env
load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), "../.env")))

# Add agents/ directory to sys.path to resolve circana_pilot_agent
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../agents")))

from circana_pilot_agent.executor import CircanaPilotExecutor
from a2a.server.agent_execution import RequestContext
from a2a.server.events import EventQueue, EventConsumer
from a2a.types import Message, Role, TextPart, DataPart, Part

import vertexai
from google.genai import types

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("web_app_server")

app = FastAPI(title="Circana Orchestrator Local Test Platform")

# Initialize Vertex AI & GenAI Client
project_id = os.environ.get("PROJECT_ID", "shade-sandbox")
location = os.environ.get("LOCATION", "us-central1")
api_endpoint = f"{location}-aiplatform.googleapis.com"

vertexai.init(
    project=project_id,
    location=location,
    api_endpoint=api_endpoint
)

genai_client = vertexai.Client(
    project=project_id,
    location=location,
    http_options=types.HttpOptions(api_version="v1beta1")
)

agent_url = os.environ.get("PRICING_AGENT_URL")

class ChatRequest(BaseModel):
    message: str
    session_id: str

class ActionRequest(BaseModel):
    action: Dict[str, Any]
    session_id: str

executor = CircanaPilotExecutor()

async def run_executor_turn(session_id: str, prompt_part: Part) -> Dict[str, Any]:
    from a2a.types import MessageSendParams
    task_id = str(uuid.uuid4())
    
    context = RequestContext(
        request=MessageSendParams(
            message=Message(
                message_id=str(uuid.uuid4()),
                role=Role.user,
                parts=[prompt_part]
            )
        ),
        context_id=session_id,
        task_id=task_id
    )
    
    event_queue = EventQueue()
    
    # Run execution
    await executor.execute(context, event_queue)
    
    # Process events
    text_response = ""
    a2ui_widgets = []
    
    consumer = EventConsumer(event_queue)
    async for ev in consumer.consume_all():
        if ev.status and ev.status.state == 'completed' and ev.status.message:
            for part in ev.status.message.parts:
                if hasattr(part, 'root'):
                    root_val = part.root
                    if hasattr(root_val, 'text') and root_val.text:
                        text_response += root_val.text + "\n"
                    elif hasattr(root_val, 'data') and root_val.data:
                        a2ui_widgets.append(root_val.data)
                elif isinstance(part, dict):
                    if "text" in part:
                        text_response += part["text"] + "\n"
                    elif "data" in part:
                        a2ui_widgets.append(part["data"])
                    elif "root" in part:
                        root_part = part["root"]
                        if isinstance(root_part, dict):
                            if "text" in root_part:
                                text_response += root_part["text"] + "\n"
                            elif "data" in root_part:
                                a2ui_widgets.append(root_part["data"])
                        
    return {
        "text": text_response.strip(),
        "widgets": a2ui_widgets
    }

@app.get("/api/sessions")
async def list_sessions():
    try:
        logger.info(f"Listing sessions for agent: {agent_url}")
        if not agent_url or "projects/" not in agent_url:
            return [
                {
                    "id": "local-session-1234",
                    "name": f"{agent_url}/sessions/local-session-1234",
                    "create_time": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    "user_id": "user"
                }
            ]
        sessions_page = genai_client.agent_engines.sessions.list(name=agent_url)
        sessions_list = []
        for s in sessions_page:
            session_id = s.name.split("/")[-1]
            sessions_list.append({
                "id": session_id,
                "name": s.name,
                "create_time": s.create_time.isoformat() if s.create_time else None,
                "user_id": s.user_id
            })
        # Sort sessions by create_time descending if available
        sessions_list.sort(key=lambda x: x["create_time"] or "", reverse=True)
        return sessions_list
    except Exception as e:
        logger.error(f"Error listing sessions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/sessions")
async def create_session():
    try:
        logger.info(f"Creating session for agent: {agent_url}")
        if not agent_url or "projects/" not in agent_url:
            session_id = f"local-session-{str(uuid.uuid4())[:8]}"
            return {
                "id": session_id,
                "name": f"{agent_url}/sessions/{session_id}",
                "create_time": datetime.datetime.now(datetime.timezone.utc).isoformat()
            }
        operation = genai_client.agent_engines.sessions.create(
            name=agent_url,
            user_id="user"
        )
        session = operation.response
        session_id = session.name.split("/")[-1]
        return {
            "id": session_id,
            "name": session.name,
            "create_time": session.create_time.isoformat() if session.create_time else None
        }
    except Exception as e:
        logger.error(f"Error creating session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sessions/{session_id}")
async def get_session_history(session_id: str):
    try:
        if not agent_url or "projects/" not in agent_url:
            return []
        session_name = f"{agent_url}/sessions/{session_id}"
        logger.info(f"Fetching history events for session: {session_name}")
        events = genai_client.agent_engines.sessions.events.list(name=session_name)
        history = []
        for ev in events:
            role = "user" if ev.author == "user" else "assistant"
            text_parts = []
            widgets = []
            
            if ev.content and ev.content.parts:
                for part in ev.content.parts:
                    if hasattr(part, 'text') and part.text:
                        text_parts.append(part.text)
            
            # Extract widgets from custom_metadata if present
            if ev.event_metadata and ev.event_metadata.custom_metadata and "widgets" in ev.event_metadata.custom_metadata:
                widgets = ev.event_metadata.custom_metadata["widgets"]
                
            history.append({
                "role": role,
                "text": "\n".join(text_parts),
                "timestamp": ev.timestamp.isoformat() if ev.timestamp else None,
                "widgets": widgets
            })
        return history
    except Exception as e:
        logger.error(f"Error fetching session history for {session_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    try:
        if not agent_url or "projects/" not in agent_url:
            return {"status": "deleted"}
        session_name = f"{agent_url}/sessions/{session_id}"
        logger.info(f"Deleting session: {session_name}")
        genai_client.agent_engines.sessions.delete(name=session_name)
        return {"status": "deleted"}
    except Exception as e:
        logger.error(f"Error deleting session {session_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    try:
        logger.info(f"Received chat request for session {req.session_id}: {req.message}")
        if not agent_url or "projects/" not in agent_url:
            result = await run_executor_turn(req.session_id, Part(root=TextPart(text=req.message)))
            return result
        session_name = f"{agent_url}/sessions/{req.session_id}"
        
        # 1. Append User Event
        try:
            genai_client.agent_engines.sessions.events.append(
                name=session_name,
                author="user",
                invocation_id=str(uuid.uuid4()),
                timestamp=datetime.datetime.now(datetime.timezone.utc),
                config={
                    "content": types.Content(
                        role="user",
                        parts=[types.Part(text=req.message)]
                    )
                }
            )
        except Exception as se:
            logger.error(f"Failed to append user message event to session: {se}")
            
        result = await run_executor_turn(req.session_id, Part(root=TextPart(text=req.message)))
        
        # 2. Append Agent Response Event
        try:
            genai_client.agent_engines.sessions.events.append(
                name=session_name,
                author="agent",
                invocation_id=str(uuid.uuid4()),
                timestamp=datetime.datetime.now(datetime.timezone.utc),
                config={
                    "content": types.Content(
                        role="model",
                        parts=[types.Part(text=result["text"])]
                    ),
                    "event_metadata": {
                        "custom_metadata": {
                            "widgets": result["widgets"]
                        }
                    }
                }
            )
        except Exception as se:
            logger.error(f"Failed to append agent response event to session: {se}")
            
        return result
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/action")
async def action_endpoint(req: ActionRequest):
    try:
        logger.info(f"Received action request for session {req.session_id}: {req.action}")
        if not agent_url or "projects/" not in agent_url:
            result = await run_executor_turn(req.session_id, Part(root=DataPart(data=req.action)))
            return result
        session_name = f"{agent_url}/sessions/{req.session_id}"
        
        # 1. Append Action click User Event
        try:
            click_desc = f"Clicked action: {req.action.get('actionId') or str(req.action)}"
            genai_client.agent_engines.sessions.events.append(
                name=session_name,
                author="user",
                invocation_id=str(uuid.uuid4()),
                timestamp=datetime.datetime.now(datetime.timezone.utc),
                config={
                    "content": types.Content(
                        role="user",
                        parts=[types.Part(text=click_desc)]
                    )
                }
            )
        except Exception as se:
            logger.error(f"Failed to append action click event to session: {se}")
            
        result = await run_executor_turn(req.session_id, Part(root=DataPart(data=req.action)))
        
        # 2. Append Agent Response Event
        try:
            genai_client.agent_engines.sessions.events.append(
                name=session_name,
                author="agent",
                invocation_id=str(uuid.uuid4()),
                timestamp=datetime.datetime.now(datetime.timezone.utc),
                config={
                    "content": types.Content(
                        role="model",
                        parts=[types.Part(text=result["text"])]
                    ),
                    "event_metadata": {
                        "custom_metadata": {
                            "widgets": result["widgets"]
                        }
                    }
                }
            )
        except Exception as se:
            logger.error(f"Failed to append agent response event to session: {se}")
            
        return result
    except Exception as e:
        logger.error(f"Error in action endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# Serve the static files from the static directory under the root URL
app.mount("/", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static"), html=True), name="static")

