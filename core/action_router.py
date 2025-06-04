"""
Action Router for dynamic follow-up action orchestration.
Routes and executes actions based on agent outputs and business rules.
"""
import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
import aiohttp
import json
from models.schemas import (
    ActionRequest, ActionResult, ActionType, UrgencyLevel,
    AgentDecision, ProcessingSession
)
from core.memory_store import get_memory_store

logger = logging.getLogger(__name__)


class ActionRouter:
    """
    Routes and executes follow-up actions based on agent decisions.
    Simulates external API calls and maintains action audit trails.
    """
    
    def __init__(self):
        self.action_handlers = {
            ActionType.ESCALATE: self._handle_escalation,
            ActionType.LOG_AND_CLOSE: self._handle_log_and_close,
            ActionType.FLAG_ANOMALY: self._handle_flag_anomaly,
            ActionType.COMPLIANCE_ALERT: self._handle_compliance_alert,
            ActionType.RISK_ALERT: self._handle_risk_alert,
            ActionType.CREATE_TICKET: self._handle_create_ticket,
        }
        self.retry_attempts = 3
        self.retry_delay = 1.0  # seconds
    
    async def route_action(self, action_request: ActionRequest) -> ActionResult:
        """
        Route and execute an action request.
        """
        action_id = str(uuid.uuid4())
        start_time = datetime.utcnow()
        
        logger.info(f"Routing action {action_request.action_type} with ID {action_id}")
        
        try:
            # Get the appropriate handler
            handler = self.action_handlers.get(action_request.action_type)
            if not handler:
                raise ValueError(f"No handler found for action type: {action_request.action_type}")
            
            # Execute the action with retry logic
            result = await self._execute_with_retry(handler, action_request)
            
            # Calculate execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Create action result
            action_result = ActionResult(
                action_id=action_id,
                action_type=action_request.action_type,
                status="success",
                response_data=result,
                execution_time_ms=execution_time
            )
            
            # Store in memory
            memory_store = await get_memory_store()
            await memory_store.increment_counter("actions_executed")
            
            logger.info(f"Action {action_id} completed successfully")
            return action_result
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            action_result = ActionResult(
                action_id=action_id,
                action_type=action_request.action_type,
                status="failed",
                error_message=str(e),
                execution_time_ms=execution_time
            )
            
            # Store failure in memory
            memory_store = await get_memory_store()
            await memory_store.increment_counter("actions_failed")
            
            logger.error(f"Action {action_id} failed: {e}")
            return action_result
    
    async def _execute_with_retry(self, handler, action_request: ActionRequest) -> Dict[str, Any]:
        """Execute action with retry logic."""
        last_exception = None
        
        for attempt in range(self.retry_attempts):
            try:
                return await handler(action_request)
            except Exception as e:
                last_exception = e
                if attempt < self.retry_attempts - 1:
                    logger.warning(f"Action attempt {attempt + 1} failed, retrying: {e}")
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                else:
                    logger.error(f"All {self.retry_attempts} attempts failed")
        
        raise last_exception
    
    async def _handle_escalation(self, action_request: ActionRequest) -> Dict[str, Any]:
        """Handle escalation actions (simulate CRM API call)."""
        payload = action_request.payload
        
        # Simulate CRM API call
        crm_data = {
            "ticket_id": str(uuid.uuid4()),
            "priority": action_request.priority.value,
            "source": action_request.source_agent,
            "description": payload.get("description", "Escalated issue"),
            "customer_info": payload.get("customer_info", {}),
            "escalation_reason": payload.get("escalation_reason", "Agent decision"),
            "assigned_to": "escalation_team",
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Simulate API call delay
        await asyncio.sleep(0.1)
        
        # Log the escalation
        logger.info(f"Escalation created: {crm_data['ticket_id']}")
        
        return {
            "crm_response": crm_data,
            "api_endpoint": "/crm/escalate",
            "status_code": 201,
            "message": "Escalation ticket created successfully"
        }
    
    async def _handle_log_and_close(self, action_request: ActionRequest) -> Dict[str, Any]:
        """Handle log and close actions."""
        payload = action_request.payload
        
        log_entry = {
            "log_id": str(uuid.uuid4()),
            "source": action_request.source_agent,
            "action": "log_and_close",
            "details": payload,
            "status": "closed",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Store in memory for audit
        memory_store = await get_memory_store()
        await memory_store.store_entry({
            "key": f"log_entry:{log_entry['log_id']}",
            "value": log_entry,
            "entry_type": "log_entry",
            "agent_source": action_request.source_agent
        })
        
        return {
            "log_entry": log_entry,
            "message": "Issue logged and closed successfully"
        }
    
    async def _handle_flag_anomaly(self, action_request: ActionRequest) -> Dict[str, Any]:
        """Handle anomaly flagging actions."""
        payload = action_request.payload
        
        anomaly_alert = {
            "alert_id": str(uuid.uuid4()),
            "anomaly_type": payload.get("anomaly_type", "data_anomaly"),
            "severity": action_request.priority.value,
            "source": action_request.source_agent,
            "details": payload.get("details", {}),
            "anomaly_score": payload.get("anomaly_score", 0.0),
            "flagged_at": datetime.utcnow().isoformat(),
            "requires_review": True
        }
        
        # Simulate alerting system API call
        await asyncio.sleep(0.05)
        
        logger.warning(f"Anomaly flagged: {anomaly_alert['alert_id']}")
        
        return {
            "anomaly_alert": anomaly_alert,
            "api_endpoint": "/alerts/anomaly",
            "status_code": 201,
            "message": "Anomaly alert created successfully"
        }
    
    async def _handle_compliance_alert(self, action_request: ActionRequest) -> Dict[str, Any]:
        """Handle compliance alert actions."""
        payload = action_request.payload
        
        compliance_alert = {
            "alert_id": str(uuid.uuid4()),
            "compliance_type": payload.get("compliance_type", "general"),
            "regulations": payload.get("regulations", []),
            "severity": "high",  # Compliance is always high priority
            "source": action_request.source_agent,
            "document_info": payload.get("document_info", {}),
            "flagged_keywords": payload.get("flagged_keywords", []),
            "created_at": datetime.utcnow().isoformat(),
            "requires_legal_review": True
        }
        
        # Simulate compliance system API call
        await asyncio.sleep(0.1)
        
        logger.critical(f"Compliance alert created: {compliance_alert['alert_id']}")
        
        return {
            "compliance_alert": compliance_alert,
            "api_endpoint": "/compliance/alert",
            "status_code": 201,
            "message": "Compliance alert created successfully"
        }
    
    async def _handle_risk_alert(self, action_request: ActionRequest) -> Dict[str, Any]:
        """Handle risk alert actions."""
        payload = action_request.payload
        
        risk_alert = {
            "alert_id": str(uuid.uuid4()),
            "risk_type": payload.get("risk_type", "financial"),
            "risk_score": payload.get("risk_score", 0.0),
            "severity": action_request.priority.value,
            "source": action_request.source_agent,
            "risk_indicators": payload.get("risk_indicators", []),
            "affected_entities": payload.get("affected_entities", []),
            "created_at": datetime.utcnow().isoformat(),
            "requires_investigation": True
        }
        
        # Simulate risk management system API call
        await asyncio.sleep(0.08)
        
        logger.warning(f"Risk alert created: {risk_alert['alert_id']}")
        
        return {
            "risk_alert": risk_alert,
            "api_endpoint": "/risk/alert",
            "status_code": 201,
            "message": "Risk alert created successfully"
        }
    
    async def _handle_create_ticket(self, action_request: ActionRequest) -> Dict[str, Any]:
        """Handle ticket creation actions."""
        payload = action_request.payload
        
        ticket = {
            "ticket_id": str(uuid.uuid4()),
            "title": payload.get("title", "Auto-generated ticket"),
            "description": payload.get("description", ""),
            "priority": action_request.priority.value,
            "category": payload.get("category", "general"),
            "source": action_request.source_agent,
            "assignee": payload.get("assignee", "auto_assignment"),
            "status": "open",
            "created_at": datetime.utcnow().isoformat(),
            "metadata": payload.get("metadata", {})
        }
        
        # Simulate ticketing system API call
        await asyncio.sleep(0.06)
        
        logger.info(f"Ticket created: {ticket['ticket_id']}")
        
        return {
            "ticket": ticket,
            "api_endpoint": "/tickets/create",
            "status_code": 201,
            "message": "Ticket created successfully"
        }
    
    async def get_action_statistics(self) -> Dict[str, Any]:
        """Get action execution statistics."""
        memory_store = await get_memory_store()
        
        stats = {
            "total_actions_executed": await memory_store.get_counter("actions_executed"),
            "total_actions_failed": await memory_store.get_counter("actions_failed"),
            "success_rate": 0.0,
            "action_types": {}
        }
        
        total = stats["total_actions_executed"]
        failed = stats["total_actions_failed"]
        
        if total > 0:
            stats["success_rate"] = ((total - failed) / total) * 100
        
        # Get action type breakdown
        for action_type in ActionType:
            count = await memory_store.get_counter(f"action_type_{action_type.value}")
            stats["action_types"][action_type.value] = count
        
        return stats


# Global action router instance
action_router = ActionRouter()


async def get_action_router() -> ActionRouter:
    """Get the global action router instance."""
    return action_router
