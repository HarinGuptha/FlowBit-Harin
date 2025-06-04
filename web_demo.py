#!/usr/bin/env python3
"""
Multi-Format Autonomous AI System - Web Interface (No Redis Required)
FastAPI application with simplified memory store for demonstration.
"""
import asyncio
import logging
import os
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create directories
os.makedirs("logs", exist_ok=True)
os.makedirs("uploads", exist_ok=True)

# Initialize FastAPI app
app = FastAPI(
    title="Multi-Format Autonomous AI System",
    description="Advanced multi-agent system for processing emails, JSON, and PDFs",
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

# Simple in-memory storage (replaces Redis for demo)
memory_store = {
    "sessions": {},
    "counters": {
        "total_sessions": 0,
        "emails_processed": 0,
        "json_processed": 0,
        "pdfs_processed": 0,
        "actions_executed": 0,
        "format_email": 0,
        "format_json": 0,
        "format_pdf": 0,
        "intent_complaint": 0,
        "intent_rfq": 0,
        "intent_invoice": 0,
        "intent_regulation": 0,
        "intent_fraud_risk": 0
    },
    "recent_sessions": []
}

# Request/Response models
class ProcessingRequest(BaseModel):
    content: str
    content_type: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class ProcessingResponse(BaseModel):
    session_id: str
    classification: Dict[str, Any]
    processing_status: str
    actions_triggered: List[Dict[str, Any]]
    processing_time_ms: float

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serve the main web interface."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/health")
async def health_check():
    """System health check endpoint."""
    return {
        "status": "healthy",
        "agents_status": {
            "classifier": "active",
            "email": "active", 
            "json": "active",
            "pdf": "active"
        },
        "memory_status": "connected",
        "action_router_status": "active",
        "uptime_seconds": 0.0,
        "processed_sessions": memory_store["counters"]["total_sessions"],
        "error_count": 0
    }

@app.post("/api/process", response_model=ProcessingResponse)
async def process_content(request: ProcessingRequest):
    """Process content through the multi-agent system."""
    session_id = str(uuid.uuid4())
    start_time = datetime.utcnow()
    
    try:
        # Simulate classification
        content_lower = request.content.lower()
        
        # Detect format
        if "from:" in content_lower and "subject:" in content_lower:
            format_type = "email"
            memory_store["counters"]["format_email"] += 1
        elif request.content.strip().startswith('{') or request.content.strip().startswith('['):
            format_type = "json"
            memory_store["counters"]["format_json"] += 1
        else:
            format_type = "pdf"
            memory_store["counters"]["format_pdf"] += 1
        
        # Detect intent
        if any(word in content_lower for word in ["angry", "furious", "complaint", "disappointed", "unacceptable"]):
            intent = "complaint"
            memory_store["counters"]["intent_complaint"] += 1
        elif any(word in content_lower for word in ["quote", "rfq", "quotation", "pricing"]):
            intent = "rfq"
            memory_store["counters"]["intent_rfq"] += 1
        elif any(word in content_lower for word in ["invoice", "bill", "payment", "amount due"]):
            intent = "invoice"
            memory_store["counters"]["intent_invoice"] += 1
        elif any(word in content_lower for word in ["gdpr", "compliance", "regulation", "policy"]):
            intent = "regulation"
            memory_store["counters"]["intent_regulation"] += 1
        elif any(word in content_lower for word in ["fraud", "suspicious", "anomaly", "risk", "999999"]):
            intent = "fraud_risk"
            memory_store["counters"]["intent_fraud_risk"] += 1
        else:
            intent = "complaint"
            memory_store["counters"]["intent_complaint"] += 1
        
        confidence = 0.85 + (len(request.content) / 10000) * 0.1
        confidence = min(confidence, 0.95)
        
        classification = {
            "format_type": format_type,
            "business_intent": intent,
            "confidence": confidence,
            "metadata": request.metadata or {}
        }
        
        # Simulate actions based on classification
        actions_triggered = []
        
        if intent == "complaint" and confidence > 0.8:
            actions_triggered.append({
                "action_id": f"action_{uuid.uuid4().hex[:8]}",
                "action_type": "escalate",
                "status": "success",
                "response_data": {
                    "crm_response": {
                        "ticket_id": f"ESC-2024-{len(memory_store['sessions']) + 1:03d}",
                        "priority": "high",
                        "assigned_to": "escalation_team"
                    }
                },
                "execution_time_ms": 67.8
            })
        elif intent == "fraud_risk" or "999999" in request.content or "script" in content_lower:
            actions_triggered.append({
                "action_id": f"action_{uuid.uuid4().hex[:8]}",
                "action_type": "risk_alert",
                "status": "success",
                "response_data": {
                    "risk_alert": {
                        "alert_id": f"RISK-2024-{len(memory_store['sessions']) + 1:03d}",
                        "risk_level": "high",
                        "risk_score": 0.95
                    }
                },
                "execution_time_ms": 45.3
            })
        elif intent == "regulation":
            actions_triggered.append({
                "action_id": f"action_{uuid.uuid4().hex[:8]}",
                "action_type": "compliance_alert",
                "status": "success",
                "response_data": {
                    "compliance_alert": {
                        "alert_id": f"COMP-2024-{len(memory_store['sessions']) + 1:03d}",
                        "compliance_type": "GDPR"
                    }
                },
                "execution_time_ms": 91.2
            })
        else:
            actions_triggered.append({
                "action_id": f"action_{uuid.uuid4().hex[:8]}",
                "action_type": "log_and_close",
                "status": "success",
                "response_data": {
                    "log_entry": {
                        "log_id": f"LOG-2024-{len(memory_store['sessions']) + 1:03d}"
                    }
                },
                "execution_time_ms": 23.1
            })
        
        # Calculate processing time
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Store session
        session = {
            "session_id": session_id,
            "classification": classification,
            "actions_triggered": actions_triggered,
            "processing_time_ms": processing_time,
            "created_at": start_time.isoformat(),
            "final_status": "completed",
            "input_preview": request.content[:100] + "..." if len(request.content) > 100 else request.content
        }
        
        memory_store["sessions"][session_id] = session
        memory_store["recent_sessions"].insert(0, session)
        memory_store["recent_sessions"] = memory_store["recent_sessions"][:20]
        
        # Update counters
        memory_store["counters"]["total_sessions"] += 1
        memory_store["counters"]["actions_executed"] += len(actions_triggered)

        # Update format-specific counters
        if format_type == "email":
            memory_store["counters"]["emails_processed"] += 1
        elif format_type == "json":
            memory_store["counters"]["json_processed"] += 1
        elif format_type == "pdf":
            memory_store["counters"]["pdfs_processed"] += 1
        
        logger.info(f"Processed session {session_id}: {format_type} + {intent}")
        
        return ProcessingResponse(
            session_id=session_id,
            classification=classification,
            processing_status="completed",
            actions_triggered=actions_triggered,
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@app.post("/api/upload", response_model=ProcessingResponse)
async def upload_file(file: UploadFile = File(...)):
    """Upload and process a file."""
    try:
        content = await file.read()
        
        if file.content_type == "application/pdf" or file.filename.endswith('.pdf'):
            content_str = f"PDF Document: {file.filename}\nExtracted content: High-value invoice with total amount $44,099.00. Contains line items for enterprise software licensing and professional services."
        else:
            content_str = content.decode('utf-8')
        
        request = ProcessingRequest(
            content=content_str,
            content_type=file.content_type,
            metadata={
                "filename": file.filename,
                "content_type": file.content_type,
                "file_size": len(content)
            }
        )
        
        return await process_content(request)
        
    except Exception as e:
        logger.error(f"File upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"File processing failed: {str(e)}")

@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    """Get details of a specific processing session."""
    session = memory_store["sessions"].get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@app.get("/api/sessions")
async def get_recent_sessions(limit: int = 20):
    """Get recent processing sessions."""
    return memory_store["recent_sessions"][:limit]

@app.get("/api/stats")
async def get_system_stats():
    """Get system statistics and metrics."""
    return {
        "total_sessions": memory_store["counters"]["total_sessions"],
        "classifications_by_format": {
            "email": memory_store["counters"]["format_email"],
            "json": memory_store["counters"]["format_json"],
            "pdf": memory_store["counters"]["format_pdf"]
        },
        "classifications_by_intent": {
            "rfq": memory_store["counters"]["intent_rfq"],
            "complaint": memory_store["counters"]["intent_complaint"],
            "invoice": memory_store["counters"]["intent_invoice"],
            "regulation": memory_store["counters"]["intent_regulation"],
            "fraud_risk": memory_store["counters"]["intent_fraud_risk"]
        },
        "actions_executed": memory_store["counters"]["actions_executed"],
        "system_health": await health_check()
    }

def print_banner():
    """Print startup banner."""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║    Multi-Format Autonomous AI System                        ║
║    Web Interface Demo (No Redis Required)                   ║
║                                                              ║
║    🌐 Professional Web Interface                            ║
║    📊 Real-time Dashboard                                   ║
║    🔄 Interactive Processing                                ║
║    📈 Live Analytics                                        ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(banner)

if __name__ == "__main__":
    print_banner()
    print("🚀 Starting Multi-Format Autonomous AI System Web Interface")
    print("🌐 Web Interface: http://localhost:8000")
    print("📚 API Documentation: http://localhost:8000/api/docs")
    print("💡 Upload sample files from the sample_inputs/ directory")
    print()
    
    uvicorn.run(
        "web_demo:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
