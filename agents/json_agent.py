"""
JSON Agent for webhook data validation and anomaly detection.
Handles schema validation, type checking, and sophisticated anomaly detection.
"""
import logging
import json
import jsonschema
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union
import numpy as np
from collections import defaultdict
from models.schemas import (
    JSONValidationResult, AgentDecision, ActionRequest, ActionType,
    UrgencyLevel, WEBHOOK_SCHEMA, INVOICE_SCHEMA
)
from core.memory_store import get_memory_store
from core.action_router import get_action_router

logger = logging.getLogger(__name__)


class JSONAgent:
    """
    Advanced JSON processing agent with schema validation,
    anomaly detection, and intelligent error handling.
    """
    
    def __init__(self):
        self.name = "json_agent"
        self.anomaly_threshold = 0.8
        
        # Schema registry for different data types
        self.schema_registry = {
            "webhook": WEBHOOK_SCHEMA,
            "invoice": INVOICE_SCHEMA,
            "transaction": {
                "type": "object",
                "required": ["id", "amount", "timestamp"],
                "properties": {
                    "id": {"type": "string"},
                    "amount": {"type": "number"},
                    "timestamp": {"type": "string"},
                    "currency": {"type": "string"},
                    "status": {"type": "string", "enum": ["pending", "completed", "failed"]}
                }
            },
            "user_event": {
                "type": "object",
                "required": ["user_id", "event_type", "timestamp"],
                "properties": {
                    "user_id": {"type": "string"},
                    "event_type": {"type": "string"},
                    "timestamp": {"type": "string"},
                    "properties": {"type": "object"}
                }
            }
        }
        
        # Anomaly detection patterns
        self.anomaly_patterns = {
            "unusual_amounts": {
                "threshold_multiplier": 3.0,  # 3x standard deviation
                "min_samples": 10
            },
            "suspicious_patterns": {
                "rapid_succession": 5,  # 5 events in short time
                "time_window_minutes": 5
            },
            "data_quality": {
                "null_percentage_threshold": 0.3,  # 30% null values
                "duplicate_threshold": 0.5  # 50% duplicates
            }
        }
        
        # Historical data for anomaly detection
        self.historical_data = defaultdict(list)
        self.data_statistics = defaultdict(dict)
    
    async def process_json(self, json_content: Union[str, Dict[str, Any]], 
                          schema_type: str = "webhook", 
                          metadata: Dict[str, Any] = None) -> Tuple[JSONValidationResult, List[ActionRequest]]:
        """
        Process JSON content with validation and anomaly detection.
        
        Args:
            json_content: JSON content as string or dict
            schema_type: Type of schema to validate against
            metadata: Additional metadata
            
        Returns:
            Tuple of (JSONValidationResult, List[ActionRequest])
        """
        start_time = datetime.utcnow()
        
        try:
            # Parse JSON if string
            if isinstance(json_content, str):
                try:
                    data = json.loads(json_content)
                except json.JSONDecodeError as e:
                    return await self._handle_invalid_json(str(e), json_content)
            else:
                data = json_content
            
            # Validate against schema
            validation_result = await self._validate_schema(data, schema_type)
            
            # Perform anomaly detection
            anomaly_result = await self._detect_anomalies(data, schema_type)
            
            # Combine results
            combined_result = JSONValidationResult(
                is_valid=validation_result.is_valid and anomaly_result["is_normal"],
                schema_errors=validation_result.schema_errors,
                anomalies=anomaly_result["anomalies"],
                anomaly_score=anomaly_result["anomaly_score"],
                missing_fields=validation_result.missing_fields,
                type_errors=validation_result.type_errors
            )
            
            # Generate actions based on results
            actions = await self._generate_actions(combined_result, data, schema_type)
            
            # Update historical data for future anomaly detection
            await self._update_historical_data(data, schema_type)
            
            # Create agent decision record
            decision = AgentDecision(
                agent_name=self.name,
                input_data={"schema_type": schema_type, "data_size": len(str(data))},
                decision=f"Valid: {combined_result.is_valid}, Anomaly Score: {combined_result.anomaly_score:.2f}",
                confidence=1.0 - combined_result.anomaly_score,
                reasoning=f"Schema validation: {len(combined_result.schema_errors)} errors, "
                         f"Anomalies detected: {len(combined_result.anomalies)}",
                execution_time_ms=(datetime.utcnow() - start_time).total_seconds() * 1000
            )
            
            # Store in memory
            memory_store = await get_memory_store()
            await memory_store.increment_counter("json_processed")
            await memory_store.increment_counter(f"schema_{schema_type}")
            
            if not combined_result.is_valid:
                await memory_store.increment_counter("json_validation_failures")
            
            if combined_result.anomaly_score > self.anomaly_threshold:
                await memory_store.increment_counter("anomalies_detected")
            
            logger.info(f"JSON processed: {schema_type}, valid: {combined_result.is_valid}, "
                       f"anomaly score: {combined_result.anomaly_score:.2f}")
            
            return combined_result, actions
            
        except Exception as e:
            logger.error(f"JSON processing failed: {e}")
            raise
    
    async def _handle_invalid_json(self, error_message: str, content: str) -> Tuple[JSONValidationResult, List[ActionRequest]]:
        """Handle invalid JSON content."""
        result = JSONValidationResult(
            is_valid=False,
            schema_errors=[f"Invalid JSON: {error_message}"],
            anomalies=["malformed_json"],
            anomaly_score=1.0,
            missing_fields=[],
            type_errors=["json_parse_error"]
        )
        
        # Create action for invalid JSON
        action = ActionRequest(
            action_type=ActionType.FLAG_ANOMALY,
            payload={
                "anomaly_type": "invalid_json",
                "error_message": error_message,
                "content_preview": content[:200] if len(content) > 200 else content,
                "details": {"error_type": "json_parse_error"}
            },
            priority=UrgencyLevel.HIGH,
            source_agent=self.name,
            correlation_id=f"json_error_{int(datetime.utcnow().timestamp())}"
        )
        
        return result, [action]
    
    async def _validate_schema(self, data: Dict[str, Any], schema_type: str) -> JSONValidationResult:
        """Validate JSON data against schema."""
        schema = self.schema_registry.get(schema_type)
        if not schema:
            logger.warning(f"No schema found for type: {schema_type}")
            return JSONValidationResult(
                is_valid=True,  # Pass if no schema
                schema_errors=[],
                anomalies=[],
                anomaly_score=0.0,
                missing_fields=[],
                type_errors=[]
            )
        
        try:
            # Validate against schema
            jsonschema.validate(data, schema)
            
            return JSONValidationResult(
                is_valid=True,
                schema_errors=[],
                anomalies=[],
                anomaly_score=0.0,
                missing_fields=[],
                type_errors=[]
            )
            
        except jsonschema.ValidationError as e:
            # Parse validation errors
            schema_errors = [str(e)]
            missing_fields = []
            type_errors = []
            
            if "required" in str(e):
                missing_field = str(e).split("'")[1] if "'" in str(e) else "unknown"
                missing_fields.append(missing_field)
            
            if "type" in str(e):
                type_errors.append(str(e))
            
            return JSONValidationResult(
                is_valid=False,
                schema_errors=schema_errors,
                anomalies=["schema_validation_failure"],
                anomaly_score=0.7,  # High anomaly score for schema failures
                missing_fields=missing_fields,
                type_errors=type_errors
            )
        
        except Exception as e:
            logger.error(f"Schema validation error: {e}")
            return JSONValidationResult(
                is_valid=False,
                schema_errors=[f"Validation error: {str(e)}"],
                anomalies=["validation_error"],
                anomaly_score=0.8,
                missing_fields=[],
                type_errors=[]
            )
    
    async def _detect_anomalies(self, data: Dict[str, Any], schema_type: str) -> Dict[str, Any]:
        """Detect anomalies in the JSON data."""
        anomalies = []
        anomaly_score = 0.0
        
        # Check for unusual amounts (if applicable)
        amount_anomaly = await self._check_amount_anomaly(data, schema_type)
        if amount_anomaly:
            anomalies.extend(amount_anomaly["anomalies"])
            anomaly_score = max(anomaly_score, amount_anomaly["score"])
        
        # Check for suspicious patterns
        pattern_anomaly = await self._check_pattern_anomaly(data, schema_type)
        if pattern_anomaly:
            anomalies.extend(pattern_anomaly["anomalies"])
            anomaly_score = max(anomaly_score, pattern_anomaly["score"])
        
        # Check data quality issues
        quality_anomaly = await self._check_data_quality(data)
        if quality_anomaly:
            anomalies.extend(quality_anomaly["anomalies"])
            anomaly_score = max(anomaly_score, quality_anomaly["score"])
        
        # Check for field type mismatches
        type_anomaly = await self._check_type_anomalies(data, schema_type)
        if type_anomaly:
            anomalies.extend(type_anomaly["anomalies"])
            anomaly_score = max(anomaly_score, type_anomaly["score"])
        
        return {
            "is_normal": anomaly_score < self.anomaly_threshold,
            "anomalies": anomalies,
            "anomaly_score": min(anomaly_score, 1.0)  # Cap at 1.0
        }
    
    async def _check_amount_anomaly(self, data: Dict[str, Any], schema_type: str) -> Optional[Dict[str, Any]]:
        """Check for unusual amounts in financial data."""
        amount_fields = ["amount", "total", "value", "price"]
        
        for field in amount_fields:
            if field in data and isinstance(data[field], (int, float)):
                amount = float(data[field])
                
                # Get historical amounts for this schema type
                historical_amounts = self.historical_data.get(f"{schema_type}_amounts", [])
                
                if len(historical_amounts) >= self.anomaly_patterns["unusual_amounts"]["min_samples"]:
                    mean_amount = np.mean(historical_amounts)
                    std_amount = np.std(historical_amounts)
                    
                    # Check if amount is unusually high or low
                    threshold = self.anomaly_patterns["unusual_amounts"]["threshold_multiplier"]
                    
                    if abs(amount - mean_amount) > threshold * std_amount:
                        return {
                            "anomalies": [f"unusual_{field}_amount"],
                            "score": min(abs(amount - mean_amount) / (threshold * std_amount), 1.0)
                        }
        
        return None
    
    async def _check_pattern_anomaly(self, data: Dict[str, Any], schema_type: str) -> Optional[Dict[str, Any]]:
        """Check for suspicious patterns like rapid succession events."""
        if "timestamp" in data:
            try:
                current_time = datetime.fromisoformat(data["timestamp"].replace('Z', '+00:00'))
                
                # Get recent events
                recent_events = self.historical_data.get(f"{schema_type}_timestamps", [])
                
                # Count events in the last few minutes
                time_window = timedelta(minutes=self.anomaly_patterns["suspicious_patterns"]["time_window_minutes"])
                recent_count = sum(1 for ts in recent_events if current_time - ts < time_window)
                
                if recent_count >= self.anomaly_patterns["suspicious_patterns"]["rapid_succession"]:
                    return {
                        "anomalies": ["rapid_succession_events"],
                        "score": min(recent_count / 10.0, 1.0)  # Normalize to 0-1
                    }
            except (ValueError, TypeError):
                return {
                    "anomalies": ["invalid_timestamp_format"],
                    "score": 0.5
                }
        
        return None
    
    async def _check_data_quality(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Check for data quality issues."""
        anomalies = []
        max_score = 0.0
        
        # Check for excessive null values
        total_fields = len(data)
        null_fields = sum(1 for value in data.values() if value is None or value == "")
        
        if total_fields > 0:
            null_percentage = null_fields / total_fields
            if null_percentage > self.anomaly_patterns["data_quality"]["null_percentage_threshold"]:
                anomalies.append("excessive_null_values")
                max_score = max(max_score, null_percentage)
        
        # Check for suspicious string patterns
        for key, value in data.items():
            if isinstance(value, str):
                # Check for SQL injection patterns
                sql_patterns = ["select ", "drop ", "insert ", "delete ", "update ", "union "]
                if any(pattern in value.lower() for pattern in sql_patterns):
                    anomalies.append("potential_sql_injection")
                    max_score = max(max_score, 0.9)
                
                # Check for script injection patterns
                script_patterns = ["<script", "javascript:", "eval(", "alert("]
                if any(pattern in value.lower() for pattern in script_patterns):
                    anomalies.append("potential_script_injection")
                    max_score = max(max_score, 0.9)
        
        if anomalies:
            return {
                "anomalies": anomalies,
                "score": max_score
            }
        
        return None
    
    async def _check_type_anomalies(self, data: Dict[str, Any], schema_type: str) -> Optional[Dict[str, Any]]:
        """Check for unexpected data types."""
        anomalies = []
        
        # Common expected types for different fields
        expected_types = {
            "id": str,
            "user_id": str,
            "amount": (int, float),
            "timestamp": str,
            "count": int,
            "active": bool,
            "email": str
        }
        
        for field, expected_type in expected_types.items():
            if field in data:
                if not isinstance(data[field], expected_type):
                    anomalies.append(f"unexpected_type_{field}")
        
        if anomalies:
            return {
                "anomalies": anomalies,
                "score": len(anomalies) * 0.2  # 0.2 per type mismatch
            }
        
        return None
    
    async def _update_historical_data(self, data: Dict[str, Any], schema_type: str):
        """Update historical data for future anomaly detection."""
        # Store amounts
        amount_fields = ["amount", "total", "value", "price"]
        for field in amount_fields:
            if field in data and isinstance(data[field], (int, float)):
                key = f"{schema_type}_amounts"
                self.historical_data[key].append(float(data[field]))
                
                # Keep only last 1000 entries
                if len(self.historical_data[key]) > 1000:
                    self.historical_data[key] = self.historical_data[key][-1000:]
        
        # Store timestamps
        if "timestamp" in data:
            try:
                timestamp = datetime.fromisoformat(data["timestamp"].replace('Z', '+00:00'))
                key = f"{schema_type}_timestamps"
                self.historical_data[key].append(timestamp)
                
                # Keep only last 100 timestamps
                if len(self.historical_data[key]) > 100:
                    self.historical_data[key] = self.historical_data[key][-100:]
            except (ValueError, TypeError):
                pass
    
    async def _generate_actions(self, result: JSONValidationResult, data: Dict[str, Any], 
                               schema_type: str) -> List[ActionRequest]:
        """Generate actions based on validation and anomaly results."""
        actions = []
        
        if not result.is_valid or result.anomaly_score > self.anomaly_threshold:
            # Create anomaly flag action
            action = ActionRequest(
                action_type=ActionType.FLAG_ANOMALY,
                payload={
                    "anomaly_type": "json_validation_anomaly",
                    "schema_type": schema_type,
                    "anomaly_score": result.anomaly_score,
                    "details": {
                        "schema_errors": result.schema_errors,
                        "anomalies": result.anomalies,
                        "missing_fields": result.missing_fields,
                        "type_errors": result.type_errors
                    },
                    "data_preview": str(data)[:500]  # First 500 chars
                },
                priority=UrgencyLevel.HIGH if result.anomaly_score > 0.8 else UrgencyLevel.MEDIUM,
                source_agent=self.name,
                correlation_id=f"json_anomaly_{hash(str(data))}_{int(datetime.utcnow().timestamp())}"
            )
            actions.append(action)
        
        # Check for specific high-risk anomalies
        high_risk_anomalies = [
            "potential_sql_injection", "potential_script_injection",
            "rapid_succession_events", "unusual_amount"
        ]
        
        if any(anomaly in result.anomalies for anomaly in high_risk_anomalies):
            # Create risk alert
            risk_action = ActionRequest(
                action_type=ActionType.RISK_ALERT,
                payload={
                    "risk_type": "data_security",
                    "risk_score": result.anomaly_score,
                    "risk_indicators": result.anomalies,
                    "affected_entities": [data.get("user_id", "unknown")],
                    "data_context": {
                        "schema_type": schema_type,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                },
                priority=UrgencyLevel.CRITICAL,
                source_agent=self.name,
                correlation_id=f"json_risk_{hash(str(data))}_{int(datetime.utcnow().timestamp())}"
            )
            actions.append(risk_action)
        
        return actions


# Global JSON agent instance
json_agent = JSONAgent()


async def get_json_agent() -> JSONAgent:
    """Get the global JSON agent instance."""
    return json_agent
