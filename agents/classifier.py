"""
Classifier Agent for format and business intent detection.
Uses few-shot learning and schema matching for accurate classification.
"""
import logging
import re
import json
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import PyPDF2
import io
from models.schemas import (
    FormatType, BusinessIntent, ClassificationResult, 
    WEBHOOK_SCHEMA, INVOICE_SCHEMA
)
from core.memory_store import get_memory_store

logger = logging.getLogger(__name__)


class ClassifierAgent:
    """
    Advanced classifier agent that detects format and business intent
    using few-shot examples and sophisticated pattern matching.
    """
    
    def __init__(self):
        self.name = "classifier_agent"
        self.confidence_threshold = 0.7
        
        # Few-shot examples for intent classification
        self.intent_examples = {
            BusinessIntent.RFQ: [
                "request for quote", "rfq", "quotation", "pricing", "estimate",
                "proposal", "bid", "cost", "price list", "quote request"
            ],
            BusinessIntent.COMPLAINT: [
                "complaint", "issue", "problem", "dissatisfied", "unhappy",
                "poor service", "defective", "broken", "not working", "angry"
            ],
            BusinessIntent.INVOICE: [
                "invoice", "bill", "payment", "amount due", "total",
                "line items", "invoice number", "billing", "charges"
            ],
            BusinessIntent.REGULATION: [
                "gdpr", "hipaa", "sox", "pci-dss", "compliance", "regulation",
                "policy", "legal", "audit", "fda", "sec", "privacy"
            ],
            BusinessIntent.FRAUD_RISK: [
                "fraud", "suspicious", "unusual activity", "risk", "alert",
                "anomaly", "security", "unauthorized", "breach", "threat"
            ]
        }
        
        # Format detection patterns
        self.format_patterns = {
            FormatType.EMAIL: {
                "headers": ["from:", "to:", "subject:", "date:"],
                "mime_types": ["message/rfc822", "text/plain", "text/html"],
                "structure_indicators": ["@", "reply-to", "cc:", "bcc:"]
            },
            FormatType.JSON: {
                "structure_indicators": ["{", "}", "[", "]", ":", ","],
                "content_types": ["application/json", "text/json"],
                "validation_keys": ["event_type", "data", "timestamp"]
            },
            FormatType.PDF: {
                "magic_bytes": [b"%PDF"],
                "extensions": [".pdf"],
                "content_indicators": ["PDF", "stream", "endstream"]
            }
        }
    
    async def classify(self, content: Any, metadata: Dict[str, Any] = None) -> ClassificationResult:
        """
        Classify input content for format and business intent.
        
        Args:
            content: Input content (string, bytes, or file-like object)
            metadata: Additional metadata about the content
            
        Returns:
            ClassificationResult with format, intent, and confidence scores
        """
        start_time = datetime.utcnow()
        
        try:
            # Detect format first
            format_type, format_confidence = await self._detect_format(content, metadata)
            
            # Extract text content for intent analysis
            text_content = await self._extract_text_content(content, format_type)
            
            # Detect business intent
            business_intent, intent_confidence = await self._detect_intent(text_content)
            
            # Calculate overall confidence
            overall_confidence = (format_confidence + intent_confidence) / 2
            
            # Create classification result
            result = ClassificationResult(
                format_type=format_type,
                business_intent=business_intent,
                confidence=overall_confidence,
                metadata={
                    "format_confidence": format_confidence,
                    "intent_confidence": intent_confidence,
                    "text_length": len(text_content) if text_content else 0,
                    "processing_time_ms": (datetime.utcnow() - start_time).total_seconds() * 1000,
                    **(metadata or {})
                }
            )
            
            # Store classification in memory
            memory_store = await get_memory_store()
            await memory_store.increment_counter("classifications_performed")
            await memory_store.increment_counter(f"format_{format_type.value}")
            await memory_store.increment_counter(f"intent_{business_intent.value}")
            
            logger.info(f"Classification completed: {format_type.value} + {business_intent.value} "
                       f"(confidence: {overall_confidence:.2f})")
            
            return result
            
        except Exception as e:
            logger.error(f"Classification failed: {e}")
            # Return default classification with low confidence
            return ClassificationResult(
                format_type=FormatType.JSON,  # Default fallback
                business_intent=BusinessIntent.COMPLAINT,  # Default fallback
                confidence=0.1,
                metadata={"error": str(e), **(metadata or {})}
            )
    
    async def _detect_format(self, content: Any, metadata: Dict[str, Any] = None) -> Tuple[FormatType, float]:
        """Detect the format of the input content."""
        
        # Check metadata first
        if metadata:
            content_type = metadata.get("content_type", "").lower()
            filename = metadata.get("filename", "").lower()
            
            if "pdf" in content_type or filename.endswith(".pdf"):
                return FormatType.PDF, 0.95
            elif "json" in content_type or filename.endswith(".json"):
                return FormatType.JSON, 0.95
            elif "email" in content_type or "message" in content_type:
                return FormatType.EMAIL, 0.95
        
        # Analyze content directly
        if isinstance(content, bytes):
            # Check for PDF magic bytes
            if content.startswith(b"%PDF"):
                return FormatType.PDF, 0.9
            
            # Try to decode as text for further analysis
            try:
                content = content.decode('utf-8')
            except UnicodeDecodeError:
                # If can't decode, likely binary (PDF)
                return FormatType.PDF, 0.8
        
        if isinstance(content, str):
            content_lower = content.lower().strip()
            
            # Check for JSON structure
            if self._is_json_format(content):
                return FormatType.JSON, 0.85
            
            # Check for email structure
            if self._is_email_format(content):
                return FormatType.EMAIL, 0.85
            
            # Check for PDF text content
            if any(indicator in content_lower for indicator in ["pdf", "stream", "endstream"]):
                return FormatType.PDF, 0.7
        
        # Default to JSON if uncertain
        return FormatType.JSON, 0.5
    
    def _is_json_format(self, content: str) -> bool:
        """Check if content is valid JSON format."""
        try:
            json.loads(content)
            return True
        except (json.JSONDecodeError, TypeError):
            # Check for JSON-like structure even if not valid JSON
            content_stripped = content.strip()
            return (content_stripped.startswith('{') and content_stripped.endswith('}')) or \
                   (content_stripped.startswith('[') and content_stripped.endswith(']'))
    
    def _is_email_format(self, content: str) -> bool:
        """Check if content is email format."""
        email_indicators = [
            "from:", "to:", "subject:", "date:",
            "@", "reply-to:", "cc:", "bcc:"
        ]
        
        content_lower = content.lower()
        indicator_count = sum(1 for indicator in email_indicators if indicator in content_lower)
        
        # If we have multiple email indicators, likely an email
        return indicator_count >= 2
    
    async def _extract_text_content(self, content: Any, format_type: FormatType) -> str:
        """Extract text content based on detected format."""
        
        if format_type == FormatType.PDF:
            return await self._extract_pdf_text(content)
        elif format_type == FormatType.EMAIL:
            return await self._extract_email_text(content)
        elif format_type == FormatType.JSON:
            return await self._extract_json_text(content)
        else:
            # Fallback to string conversion
            return str(content) if content else ""
    
    async def _extract_pdf_text(self, content: Any) -> str:
        """Extract text from PDF content."""
        try:
            if isinstance(content, bytes):
                pdf_file = io.BytesIO(content)
            elif isinstance(content, str):
                # If string, assume it's already extracted text
                return content
            else:
                pdf_file = content
            
            reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            
            return text.strip()
        except Exception as e:
            logger.warning(f"Failed to extract PDF text: {e}")
            return str(content) if content else ""
    
    async def _extract_email_text(self, content: Any) -> str:
        """Extract text from email content."""
        try:
            if isinstance(content, str):
                # Try to parse as email
                msg = email.message_from_string(content)
                
                # Extract subject and body
                subject = msg.get("Subject", "")
                body = ""
                
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            body += part.get_payload(decode=True).decode('utf-8', errors='ignore')
                else:
                    body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
                
                return f"Subject: {subject}\n\n{body}".strip()
            else:
                return str(content)
        except Exception as e:
            logger.warning(f"Failed to extract email text: {e}")
            return str(content) if content else ""
    
    async def _extract_json_text(self, content: Any) -> str:
        """Extract meaningful text from JSON content."""
        try:
            if isinstance(content, str):
                data = json.loads(content)
            else:
                data = content
            
            # Extract text values from JSON recursively
            text_parts = []
            self._extract_text_from_dict(data, text_parts)
            
            return " ".join(text_parts)
        except Exception as e:
            logger.warning(f"Failed to extract JSON text: {e}")
            return str(content) if content else ""
    
    def _extract_text_from_dict(self, obj: Any, text_parts: List[str]):
        """Recursively extract text from dictionary/list structures."""
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, str):
                    text_parts.append(value)
                elif isinstance(value, (dict, list)):
                    self._extract_text_from_dict(value, text_parts)
        elif isinstance(obj, list):
            for item in obj:
                self._extract_text_from_dict(item, text_parts)
        elif isinstance(obj, str):
            text_parts.append(obj)
    
    async def _detect_intent(self, text_content: str) -> Tuple[BusinessIntent, float]:
        """Detect business intent from text content."""
        if not text_content:
            return BusinessIntent.COMPLAINT, 0.3  # Default with low confidence
        
        text_lower = text_content.lower()
        intent_scores = {}
        
        # Calculate scores for each intent based on keyword matching
        for intent, keywords in self.intent_examples.items():
            score = 0
            for keyword in keywords:
                if keyword in text_lower:
                    # Weight longer keywords more heavily
                    score += len(keyword.split()) * 0.1
            
            # Normalize score by text length
            if len(text_content) > 0:
                intent_scores[intent] = min(score / (len(text_content) / 100), 1.0)
            else:
                intent_scores[intent] = 0
        
        # Find the intent with highest score
        if intent_scores:
            best_intent = max(intent_scores, key=intent_scores.get)
            confidence = intent_scores[best_intent]
            
            # Apply minimum confidence threshold
            if confidence < 0.3:
                confidence = 0.3
            
            return best_intent, confidence
        
        # Default fallback
        return BusinessIntent.COMPLAINT, 0.3


# Global classifier instance
classifier_agent = ClassifierAgent()


async def get_classifier_agent() -> ClassifierAgent:
    """Get the global classifier agent instance."""
    return classifier_agent
