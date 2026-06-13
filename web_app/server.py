import os
import sys
import uuid
import logging
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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("web_app_server")

app = FastAPI(title="Circana Orchestrator Local Test Platform")

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
                if hasattr(part.root, 'text') and part.root.text:
                    text_response += part.root.text + "\n"
                elif hasattr(part.root, 'data') and part.root.data:
                    a2ui_widgets.append(part.root.data)
                    
    return {
        "text": text_response.strip(),
        "widgets": a2ui_widgets
    }

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    try:
        logger.info(f"Received chat request for session {req.session_id}: {req.message}")
        result = await run_executor_turn(req.session_id, Part(root=TextPart(text=req.message)))
        return result
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/action")
async def action_endpoint(req: ActionRequest):
    try:
        logger.info(f"Received action request for session {req.session_id}: {req.action}")
        result = await run_executor_turn(req.session_id, Part(root=DataPart(data=req.action)))
        return result
    except Exception as e:
        logger.error(f"Error in action endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# Serve the static files from the static directory under the root URL
app.mount("/", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static"), html=True), name="static")
