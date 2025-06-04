"""
Email Agent for processing emails with advanced tone analysis and entity extraction.
Handles email parsing, sentiment analysis, and escalation decisions.
"""
import logging
import re
import email
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from email.utils import parseaddr, parsedate_to_datetime
import textstat
from models.schemas import (
    EmailData, EmailAnalysis, ToneType, UrgencyLevel, 
    AgentDecision, ActionRequest, ActionType
)
from core.memory_store import get_memory_store
from core.action_router import get_action_router

logger = logging.getLogger(__name__)


class EmailAgent:
    """
    Advanced email processing agent with sophisticated tone analysis,
    sentiment detection, and automated escalation logic.
    """
    
    def __init__(self):
        self.name = "email_agent"
        
        # Tone detection patterns
        self.tone_patterns = {
            ToneType.ANGRY: [
                "angry", "furious", "outraged", "disgusted", "hate", "terrible",
                "awful", "worst", "horrible", "unacceptable", "ridiculous",
                "pathetic", "useless", "incompetent", "fed up"
            ],
            ToneType.THREATENING: [
                "lawsuit", "legal action", "attorney", "lawyer", "sue", "court",
                "report you", "better business bureau", "media", "social media",
                "review", "complaint", "authorities", "regulator"
            ],
            ToneType.ESCALATION: [
                "manager", "supervisor", "escalate", "higher up", "corporate",
                "headquarters", "ceo", "president", "director", "urgent",
                "immediate attention", "asap", "emergency"
            ],
            ToneType.URGENT: [
                "urgent", "asap", "immediately", "emergency", "critical",
                "time sensitive", "deadline", "rush", "priority", "important"
            ],
            ToneType.POLITE: [
                "please", "thank you", "appreciate", "grateful", "kindly",
                "would you", "could you", "if possible", "at your convenience",
                "respectfully", "sincerely", "best regards"
            ]
        }
        
        # Urgency indicators
        self.urgency_indicators = {
            UrgencyLevel.CRITICAL: [
                "emergency", "critical", "system down", "outage", "breach",
                "security incident", "data loss", "urgent", "asap"
            ],
            UrgencyLevel.HIGH: [
                "urgent", "high priority", "important", "time sensitive",
                "deadline", "escalation", "manager", "supervisor"
            ],
            UrgencyLevel.MEDIUM: [
                "soon", "when possible", "follow up", "update", "status",
                "question", "inquiry", "request"
            ],
            UrgencyLevel.LOW: [
                "whenever", "no rush", "convenience", "general", "information",
                "fyi", "for your information"
            ]
        }
        
        # Entity extraction patterns
        self.entity_patterns = {
            "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "phone": r'\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b',
            "order_id": r'\b(?:order|invoice|ticket|ref|reference)[\s#:]*([A-Z0-9-]{6,})\b',
            "amount": r'\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            "date": r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b',
            "account": r'\b(?:account|acct)[\s#:]*([A-Z0-9-]{6,})\b'
        }
    
    async def process_email(self, email_content: str, metadata: Dict[str, Any] = None) -> Tuple[EmailData, EmailAnalysis, List[ActionRequest]]:
        """
        Process email content and return structured data, analysis, and recommended actions.
        
        Args:
            email_content: Raw email content
            metadata: Additional metadata about the email
            
        Returns:
            Tuple of (EmailData, EmailAnalysis, List[ActionRequest])
        """
        start_time = datetime.utcnow()
        
        try:
            # Parse email structure
            email_data = await self._parse_email_structure(email_content)
            
            # Perform comprehensive analysis
            analysis = await self._analyze_email(email_data)
            
            # Generate action recommendations
            actions = await self._generate_actions(email_data, analysis)
            
            # Create agent decision record
            decision = AgentDecision(
                agent_name=self.name,
                input_data={"email_subject": email_data.subject, "sender": str(email_data.sender)},
                decision=f"Tone: {analysis.tone.value}, Urgency: {analysis.urgency.value}",
                confidence=0.8,  # Base confidence
                reasoning=f"Detected {analysis.tone.value} tone with {analysis.urgency.value} urgency. "
                         f"Sentiment score: {analysis.sentiment_score:.2f}",
                execution_time_ms=(datetime.utcnow() - start_time).total_seconds() * 1000
            )
            
            # Store in memory
            memory_store = await get_memory_store()
            await memory_store.increment_counter("emails_processed")
            await memory_store.increment_counter(f"tone_{analysis.tone.value}")
            await memory_store.increment_counter(f"urgency_{analysis.urgency.value}")
            
            logger.info(f"Email processed: {analysis.tone.value} tone, {analysis.urgency.value} urgency")
            
            return email_data, analysis, actions
            
        except Exception as e:
            logger.error(f"Email processing failed: {e}")
            raise
    
    async def _parse_email_structure(self, email_content: str) -> EmailData:
        """Parse email content into structured data."""
        try:
            # Parse email message
            msg = email.message_from_string(email_content)
            
            # Extract basic fields
            sender_raw = msg.get("From", "")
            sender_name, sender_email = parseaddr(sender_raw)
            
            recipient_raw = msg.get("To", "")
            recipient_name, recipient_email = parseaddr(recipient_raw) if recipient_raw else (None, None)
            
            subject = msg.get("Subject", "")
            
            # Extract timestamp
            date_header = msg.get("Date")
            timestamp = None
            if date_header:
                try:
                    timestamp = parsedate_to_datetime(date_header)
                except:
                    timestamp = datetime.utcnow()
            else:
                timestamp = datetime.utcnow()
            
            # Extract body content
            body = ""
            attachments = []
            
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition", ""))
                    
                    if content_type == "text/plain" and "attachment" not in content_disposition:
                        try:
                            body += part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        except:
                            body += str(part.get_payload())
                    elif "attachment" in content_disposition:
                        filename = part.get_filename()
                        if filename:
                            attachments.append(filename)
            else:
                try:
                    body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
                except:
                    body = str(msg.get_payload())
            
            return EmailData(
                sender=sender_email or "unknown@example.com",
                recipient=recipient_email,
                subject=subject,
                body=body.strip(),
                timestamp=timestamp,
                attachments=attachments
            )
            
        except Exception as e:
            logger.warning(f"Failed to parse email structure: {e}")
            # Return basic structure from raw content
            lines = email_content.split('\n')
            subject = next((line.split(':', 1)[1].strip() for line in lines if line.lower().startswith('subject:')), "")
            sender = next((line.split(':', 1)[1].strip() for line in lines if line.lower().startswith('from:')), "unknown@example.com")
            
            # Extract sender email if in format "Name <email>"
            email_match = re.search(r'<([^>]+)>', sender)
            if email_match:
                sender = email_match.group(1)
            
            return EmailData(
                sender=sender,
                subject=subject,
                body=email_content,
                timestamp=datetime.utcnow()
            )
    
    async def _analyze_email(self, email_data: EmailData) -> EmailAnalysis:
        """Perform comprehensive email analysis."""
        
        # Combine subject and body for analysis
        full_text = f"{email_data.subject} {email_data.body}".lower()
        
        # Detect tone
        tone = await self._detect_tone(full_text)
        
        # Detect urgency
        urgency = await self._detect_urgency(full_text, tone)
        
        # Calculate sentiment score
        sentiment_score = await self._calculate_sentiment(full_text)
        
        # Extract key phrases
        key_phrases = await self._extract_key_phrases(full_text)
        
        # Categorize issue
        issue_category = await self._categorize_issue(full_text)
        
        # Determine if escalation is required
        requires_escalation = await self._requires_escalation(tone, urgency, sentiment_score)
        
        # Extract entities
        extracted_entities = await self._extract_entities(email_data.body)
        
        return EmailAnalysis(
            tone=tone,
            urgency=urgency,
            sentiment_score=sentiment_score,
            key_phrases=key_phrases,
            issue_category=issue_category,
            requires_escalation=requires_escalation,
            extracted_entities=extracted_entities
        )
    
    async def _detect_tone(self, text: str) -> ToneType:
        """Detect the tone of the email."""
        tone_scores = {}
        
        for tone_type, patterns in self.tone_patterns.items():
            score = sum(1 for pattern in patterns if pattern in text)
            tone_scores[tone_type] = score
        
        # Find the tone with the highest score
        if tone_scores and max(tone_scores.values()) > 0:
            return max(tone_scores, key=tone_scores.get)
        
        # Default to neutral if no specific tone detected
        return ToneType.NEUTRAL
    
    async def _detect_urgency(self, text: str, tone: ToneType) -> UrgencyLevel:
        """Detect urgency level based on content and tone."""
        urgency_scores = {}
        
        for urgency_level, patterns in self.urgency_indicators.items():
            score = sum(1 for pattern in patterns if pattern in text)
            urgency_scores[urgency_level] = score
        
        # Adjust based on tone
        if tone in [ToneType.ANGRY, ToneType.THREATENING]:
            urgency_scores[UrgencyLevel.HIGH] = urgency_scores.get(UrgencyLevel.HIGH, 0) + 2
        elif tone == ToneType.ESCALATION:
            urgency_scores[UrgencyLevel.CRITICAL] = urgency_scores.get(UrgencyLevel.CRITICAL, 0) + 3
        elif tone == ToneType.URGENT:
            urgency_scores[UrgencyLevel.HIGH] = urgency_scores.get(UrgencyLevel.HIGH, 0) + 1
        
        # Find the urgency with the highest score
        if urgency_scores and max(urgency_scores.values()) > 0:
            return max(urgency_scores, key=urgency_scores.get)
        
        # Default to medium urgency
        return UrgencyLevel.MEDIUM
    
    async def _calculate_sentiment(self, text: str) -> float:
        """Calculate sentiment score (-1 to 1)."""
        # Simple sentiment analysis based on positive/negative words
        positive_words = [
            "good", "great", "excellent", "amazing", "wonderful", "fantastic",
            "pleased", "satisfied", "happy", "love", "appreciate", "thank"
        ]
        
        negative_words = [
            "bad", "terrible", "awful", "horrible", "hate", "angry", "frustrated",
            "disappointed", "upset", "annoyed", "disgusted", "furious", "worst"
        ]
        
        words = text.split()
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)
        
        total_sentiment_words = positive_count + negative_count
        if total_sentiment_words == 0:
            return 0.0  # Neutral
        
        return (positive_count - negative_count) / total_sentiment_words
    
    async def _extract_key_phrases(self, text: str) -> List[str]:
        """Extract key phrases from the email."""
        # Simple key phrase extraction based on common patterns
        phrases = []
        
        # Extract phrases in quotes
        quoted_phrases = re.findall(r'"([^"]*)"', text)
        phrases.extend(quoted_phrases)
        
        # Extract capitalized phrases (potential product names, etc.)
        capitalized_phrases = re.findall(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', text)
        phrases.extend(capitalized_phrases)
        
        # Extract common issue phrases
        issue_phrases = [
            "not working", "broken", "error", "problem", "issue", "bug",
            "can't access", "unable to", "doesn't work", "failed to"
        ]
        
        for phrase in issue_phrases:
            if phrase in text:
                phrases.append(phrase)
        
        return list(set(phrases))[:10]  # Return unique phrases, max 10
    
    async def _categorize_issue(self, text: str) -> Optional[str]:
        """Categorize the type of issue."""
        categories = {
            "technical": ["error", "bug", "not working", "broken", "system", "website", "app"],
            "billing": ["invoice", "charge", "payment", "bill", "refund", "money"],
            "service": ["service", "support", "help", "assistance", "representative"],
            "product": ["product", "item", "order", "delivery", "shipping", "quality"],
            "account": ["account", "login", "password", "access", "profile", "settings"]
        }
        
        category_scores = {}
        for category, keywords in categories.items():
            score = sum(1 for keyword in keywords if keyword in text)
            category_scores[category] = score
        
        if category_scores and max(category_scores.values()) > 0:
            return max(category_scores, key=category_scores.get)
        
        return None
    
    async def _requires_escalation(self, tone: ToneType, urgency: UrgencyLevel, sentiment_score: float) -> bool:
        """Determine if the email requires escalation."""
        escalation_conditions = [
            tone in [ToneType.ANGRY, ToneType.THREATENING, ToneType.ESCALATION],
            urgency in [UrgencyLevel.CRITICAL, UrgencyLevel.HIGH],
            sentiment_score < -0.5
        ]
        
        # Escalate if any condition is met
        return any(escalation_conditions)
    
    async def _extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract entities using regex patterns."""
        entities = {}
        
        for entity_type, pattern in self.entity_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                entities[entity_type] = list(set(matches))  # Remove duplicates
        
        return entities
    
    async def _generate_actions(self, email_data: EmailData, analysis: EmailAnalysis) -> List[ActionRequest]:
        """Generate action recommendations based on analysis."""
        actions = []
        
        if analysis.requires_escalation:
            # Create escalation action
            escalation_action = ActionRequest(
                action_type=ActionType.ESCALATE,
                payload={
                    "description": f"Email escalation required: {analysis.tone.value} tone detected",
                    "customer_info": {
                        "email": str(email_data.sender),
                        "subject": email_data.subject
                    },
                    "escalation_reason": f"Tone: {analysis.tone.value}, Urgency: {analysis.urgency.value}",
                    "sentiment_score": analysis.sentiment_score,
                    "issue_category": analysis.issue_category
                },
                priority=analysis.urgency,
                source_agent=self.name,
                correlation_id=f"email_{hash(email_data.subject)}_{int(datetime.utcnow().timestamp())}"
            )
            actions.append(escalation_action)
        else:
            # Create log and close action for routine emails
            log_action = ActionRequest(
                action_type=ActionType.LOG_AND_CLOSE,
                payload={
                    "email_summary": {
                        "sender": str(email_data.sender),
                        "subject": email_data.subject,
                        "tone": analysis.tone.value,
                        "urgency": analysis.urgency.value,
                        "sentiment_score": analysis.sentiment_score,
                        "issue_category": analysis.issue_category
                    },
                    "resolution": "Routine email processed and logged"
                },
                priority=analysis.urgency,
                source_agent=self.name,
                correlation_id=f"email_{hash(email_data.subject)}_{int(datetime.utcnow().timestamp())}"
            )
            actions.append(log_action)
        
        return actions


# Global email agent instance
email_agent = EmailAgent()


async def get_email_agent() -> EmailAgent:
    """Get the global email agent instance."""
    return email_agent
