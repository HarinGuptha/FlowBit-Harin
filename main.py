"""
Multi-Format Autonomous AI System with Contextual Decisioning & Chained Actions
FastAPI application entry point with professional web interface.
"""
import asyncio
import logging
import os
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import aiofiles

# Import our agents and core components
from agents import get_classifier_agent, get_email_agent, get_json_agent, get_pdf_agent
from core import get_memory_store, get_action_router
from models.schemas import (
    ProcessingSession, ClassificationResult, FormatType, BusinessIntent,
    SystemHealth, ActionResult
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create directories
os.makedirs("logs", exist_ok=True)
os.makedirs("uploads", exist_ok=True)
os.makedirs("static", exist_ok=True)
os.makedirs("templates", exist_ok=True)

# Initialize FastAPI app
app = FastAPI(
    title="Multi-Format Autonomous AI System",
    description="Advanced multi-agent system for processing emails, JSON, and PDFs with contextual decisioning",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Request/Response models
class ProcessingRequest(BaseModel):
    content: str
    content_type: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class ProcessingResponse(BaseModel):
    session_id: str
    classification: ClassificationResult
    processing_status: str
    actions_triggered: List[ActionResult]
    processing_time_ms: float

class SystemStatsResponse(BaseModel):
    total_sessions: int
    classifications_by_format: Dict[str, int]
    classifications_by_intent: Dict[str, int]
    actions_executed: int
    system_health: SystemHealth


@app.on_event("startup")
async def startup_event():
    """Initialize system components on startup."""
    try:
        # Initialize memory store
        memory_store = await get_memory_store()
        logger.info("Memory store initialized")
        
        # Initialize agents
        await get_classifier_agent()
        await get_email_agent()
        await get_json_agent()
        await get_pdf_agent()
        logger.info("All agents initialized")
        
        # Initialize action router
        await get_action_router()
        logger.info("Action router initialized")
        
        logger.info("Multi-agent system startup completed successfully")
        
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    try:
        memory_store = await get_memory_store()
        await memory_store.disconnect()
        logger.info("System shutdown completed")
    except Exception as e:
        logger.error(f"Shutdown error: {e}")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serve the main web interface."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/health")
async def health_check():
    """System health check endpoint."""
    try:
        memory_store = await get_memory_store()
        stats = await memory_store.get_system_stats()
        
        health = SystemHealth(
            status="healthy",
            agents_status={
                "classifier": "active",
                "email": "active", 
                "json": "active",
                "pdf": "active"
            },
            memory_status="connected" if memory_store.is_connected else "disconnected",
            action_router_status="active",
            uptime_seconds=0.0,  # Would track actual uptime in production
            processed_sessions=stats.get("total_sessions", 0),
            error_count=stats.get("counters", {}).get("errors", 0)
        )
        
        return health
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return SystemHealth(
            status="unhealthy",
            agents_status={},
            memory_status="error",
            action_router_status="error",
            uptime_seconds=0.0,
            processed_sessions=0,
            error_count=1
        )


@app.post("/api/process", response_model=ProcessingResponse)
async def process_content(
    request: ProcessingRequest,
    background_tasks: BackgroundTasks
):
    """Process content through the multi-agent system."""
    session_id = str(uuid.uuid4())
    start_time = datetime.utcnow()
    
    try:
        logger.info(f"Starting processing session: {session_id}")
        
        # Step 1: Classify the content
        classifier = await get_classifier_agent()
        classification = await classifier.classify(
            content=request.content,
            metadata=request.metadata
        )
        
        # Step 2: Route to appropriate agent based on format
        actions_triggered = []
        
        if classification.format_type == FormatType.EMAIL:
            email_agent = await get_email_agent()
            email_data, email_analysis, email_actions = await email_agent.process_email(
                request.content, request.metadata
            )
            
            # Execute actions
            action_router = await get_action_router()
            for action_request in email_actions:
                action_result = await action_router.route_action(action_request)
                actions_triggered.append(action_result)
        
        elif classification.format_type == FormatType.JSON:
            json_agent = await get_json_agent()
            json_result, json_actions = await json_agent.process_json(
                request.content, metadata=request.metadata
            )
            
            # Execute actions
            action_router = await get_action_router()
            for action_request in json_actions:
                action_result = await action_router.route_action(action_request)
                actions_triggered.append(action_result)
        
        elif classification.format_type == FormatType.PDF:
            # For API, we expect base64 encoded PDF content
            import base64
            try:
                pdf_bytes = base64.b64decode(request.content)
                pdf_agent = await get_pdf_agent()
                pdf_analysis, pdf_actions = await pdf_agent.process_pdf(
                    pdf_bytes, request.metadata
                )
                
                # Execute actions
                action_router = await get_action_router()
                for action_request in pdf_actions:
                    action_result = await action_router.route_action(action_request)
                    actions_triggered.append(action_result)
                    
            except Exception as e:
                logger.error(f"PDF processing failed: {e}")
                raise HTTPException(status_code=400, detail=f"PDF processing error: {str(e)}")
        
        # Calculate processing time
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Create and store processing session
        session = ProcessingSession(
            session_id=session_id,
            input_metadata=request.metadata or {},
            classification=classification,
            actions_triggered=actions_triggered,
            final_status="completed",
            total_processing_time_ms=processing_time,
            completed_at=datetime.utcnow()
        )
        
        # Store session in background
        background_tasks.add_task(store_session, session)
        
        logger.info(f"Processing session {session_id} completed successfully")
        
        return ProcessingResponse(
            session_id=session_id,
            classification=classification,
            processing_status="completed",
            actions_triggered=actions_triggered,
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        logger.error(f"Processing session {session_id} failed: {e}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@app.post("/api/upload", response_model=ProcessingResponse)
async def upload_file(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
):
    """Upload and process a file."""
    session_id = str(uuid.uuid4())
    
    try:
        # Read file content
        content = await file.read()
        
        # Determine content type and prepare for processing
        if file.content_type == "application/pdf" or file.filename.endswith('.pdf'):
            # For PDF, encode as base64 for API processing
            import base64
            content_str = base64.b64encode(content).decode('utf-8')
            content_type = "application/pdf"
        else:
            # For text files, decode as string
            content_str = content.decode('utf-8')
            content_type = file.content_type
        
        # Create processing request
        request = ProcessingRequest(
            content=content_str,
            content_type=content_type,
            metadata={
                "filename": file.filename,
                "content_type": file.content_type,
                "file_size": len(content)
            }
        )
        
        # Process through the system
        return await process_content(request, background_tasks)
        
    except Exception as e:
        logger.error(f"File upload processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"File processing failed: {str(e)}")


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    """Get details of a specific processing session."""
    try:
        memory_store = await get_memory_store()
        session = await memory_store.get_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return session
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve session")


@app.get("/api/sessions")
async def get_recent_sessions(limit: int = 20):
    """Get recent processing sessions."""
    try:
        memory_store = await get_memory_store()
        sessions = await memory_store.get_recent_sessions(limit)
        return sessions
        
    except Exception as e:
        logger.error(f"Failed to get recent sessions: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve sessions")


@app.get("/api/stats", response_model=SystemStatsResponse)
async def get_system_stats():
    """Get system statistics and metrics."""
    try:
        memory_store = await get_memory_store()
        stats = await memory_store.get_system_stats()
        
        # Get action router stats
        action_router = await get_action_router()
        action_stats = await action_router.get_action_statistics()
        
        # Compile response
        return SystemStatsResponse(
            total_sessions=stats.get("total_sessions", 0),
            classifications_by_format={
                "email": await memory_store.get_counter("format_email"),
                "json": await memory_store.get_counter("format_json"),
                "pdf": await memory_store.get_counter("format_pdf")
            },
            classifications_by_intent={
                "rfq": await memory_store.get_counter("intent_rfq"),
                "complaint": await memory_store.get_counter("intent_complaint"),
                "invoice": await memory_store.get_counter("intent_invoice"),
                "regulation": await memory_store.get_counter("intent_regulation"),
                "fraud_risk": await memory_store.get_counter("intent_fraud_risk")
            },
            actions_executed=action_stats.get("total_actions_executed", 0),
            system_health=await health_check()
        )
        
    except Exception as e:
        logger.error(f"Failed to get system stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")


async def store_session(session: ProcessingSession):
    """Background task to store processing session."""
    try:
        memory_store = await get_memory_store()
        await memory_store.store_session(session)
    except Exception as e:
        logger.error(f"Failed to store session {session.session_id}: {e}")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
