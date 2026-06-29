"""
FastAPI Routes for NeuralSwarm.
"""

import uuid
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from schemas.swarm import SwarmConfig
from api.streaming import stream_debate
from db.debate_log import save_session

router = APIRouter()

# In-memory store for configs to pass to SSE endpoint
session_configs = {}

@router.post("/swarm/start")
async def start_swarm(config: SwarmConfig):
    """
    Start a new NeuralSwarm debate session.
    Returns a session_id that the client uses to connect to the SSE stream.
    """
    session_id = str(uuid.uuid4())
    
    # Save session config
    session_configs[session_id] = config
    save_session(session_id, config.model_dump())
    
    return {"session_id": session_id, "message": "Session created. Connect to /swarm/stream/{session_id} to begin."}


@router.get("/swarm/stream/{session_id}")
async def stream_swarm(session_id: str):
    """
    SSE Endpoint for streaming the debate graph execution.
    """
    if session_id not in session_configs:
        raise HTTPException(status_code=404, detail="Session not found")
        
    config = session_configs.pop(session_id) # pop so it's not reused
    
    return StreamingResponse(
        stream_debate(session_id, config),
        media_type="text/event-stream",
        headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"}
    )

@router.post("/swarm/stop/{session_id}")
async def stop_swarm(session_id: str):
    from db.debate_log import update_session_status
    update_session_status(session_id, "stopped")
    return {"message": "Session stopped"}
