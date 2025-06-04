"""
PDF Agent for document parsing and compliance checking.
Handles real PDF parsing, invoice processing, and regulatory compliance detection.
"""
import logging
import re
import io
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Union
import PyPDF2
from models.schemas import (
    PDFAnalysis, AgentDecision, ActionRequest, ActionType, UrgencyLevel
)
from core.memory_store import get_memory_store
from core.action_router import get_action_router

logger = logging.getLogger(__name__)


class PDFAgent:
    """
    Advanced PDF processing agent with real PDF parsing,
    invoice analysis, and compliance checking capabilities.
    """
    
    def __init__(self):
        self.name = "pdf_agent"
        self.invoice_threshold = 10000.0  # Flag invoices over $10,000
        
        # Compliance keywords for different regulations
        self.compliance_keywords = {
            "GDPR": [
                "gdpr", "general data protection regulation", "data protection",
                "personal data", "data subject", "data controller", "data processor",
                "consent", "right to be forgotten", "data portability"
            ],
            "HIPAA": [
                "hipaa", "health insurance portability", "protected health information",
                "phi", "medical records", "healthcare", "patient data",
                "covered entity", "business associate"
            ],
            "SOX": [
                "sarbanes-oxley", "sox", "financial reporting", "internal controls",
                "audit", "financial statements", "sec", "public company"
            ],
            "PCI-DSS": [
                "pci-dss", "payment card industry", "cardholder data",
                "credit card", "payment processing", "card data security"
            ],
            "FDA": [
                "fda", "food and drug administration", "clinical trial",
                "medical device", "pharmaceutical", "drug approval",
                "adverse event", "regulatory submission"
            ]
        }
        
        # Document type patterns
        self.document_patterns = {
            "invoice": [
                "invoice", "bill", "amount due", "total", "subtotal",
                "tax", "payment terms", "due date", "invoice number"
            ],
            "contract": [
                "agreement", "contract", "terms and conditions", "party",
                "whereas", "hereby", "signature", "effective date"
            ],
            "policy": [
                "policy", "procedure", "guidelines", "standards",
                "compliance", "requirements", "shall", "must"
            ],
            "report": [
                "report", "analysis", "findings", "conclusion",
                "recommendation", "executive summary", "methodology"
            ],
            "regulation": [
                "regulation", "rule", "section", "subsection",
                "compliance", "requirement", "violation", "penalty"
            ]
        }
        
        # Invoice parsing patterns
        self.invoice_patterns = {
            "invoice_number": r"(?:invoice|inv)[\s#:]*([A-Z0-9-]+)",
            "total_amount": r"(?:total|amount due|grand total)[\s:$]*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)",
            "date": r"(?:date|invoice date)[\s:]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
            "line_item": r"(\d+(?:\.\d{2})?)\s+([^\n]+?)\s+(\d+(?:\.\d{2})?)",
            "tax": r"(?:tax|vat)[\s:$]*(\d+(?:\.\d{2})?)",
            "subtotal": r"(?:subtotal|sub total)[\s:$]*(\d+(?:\.\d{2})?)"
        }
    
    async def process_pdf(self, pdf_content: Union[bytes, io.BytesIO], 
                         metadata: Dict[str, Any] = None) -> Tuple[PDFAnalysis, List[ActionRequest]]:
        """
        Process PDF content with parsing, analysis, and compliance checking.
        
        Args:
            pdf_content: PDF content as bytes or BytesIO
            metadata: Additional metadata about the PDF
            
        Returns:
            Tuple of (PDFAnalysis, List[ActionRequest])
        """
        start_time = datetime.utcnow()
        
        try:
            # Extract text from PDF
            extracted_text = await self._extract_pdf_text(pdf_content)
            
            # Determine document type
            document_type = await self._classify_document_type(extracted_text)
            
            # Extract structured data based on document type
            structured_data = await self._extract_structured_data(extracted_text, document_type)
            
            # Check for compliance flags
            compliance_flags = await self._check_compliance(extracted_text)
            
            # Detect risk indicators
            risk_indicators = await self._detect_risk_indicators(extracted_text, structured_data)
            
            # Process invoice-specific data if applicable
            invoice_total = None
            line_items = []
            if document_type == "invoice":
                invoice_total, line_items = await self._process_invoice_data(extracted_text)
            
            # Create analysis result
            analysis = PDFAnalysis(
                document_type=document_type,
                extracted_text=extracted_text[:1000],  # Truncate for storage
                structured_data=structured_data,
                compliance_flags=compliance_flags,
                risk_indicators=risk_indicators,
                invoice_total=invoice_total,
                line_items=line_items
            )
            
            # Generate actions based on analysis
            actions = await self._generate_actions(analysis)
            
            # Create agent decision record
            decision = AgentDecision(
                agent_name=self.name,
                input_data={
                    "document_type": document_type,
                    "text_length": len(extracted_text),
                    "compliance_flags_count": len(compliance_flags)
                },
                decision=f"Document type: {document_type}, Compliance flags: {len(compliance_flags)}",
                confidence=0.85,  # Base confidence for PDF processing
                reasoning=f"Extracted {len(extracted_text)} characters, "
                         f"detected {len(compliance_flags)} compliance issues, "
                         f"found {len(risk_indicators)} risk indicators",
                execution_time_ms=(datetime.utcnow() - start_time).total_seconds() * 1000
            )
            
            # Store in memory
            memory_store = await get_memory_store()
            await memory_store.increment_counter("pdfs_processed")
            await memory_store.increment_counter(f"document_type_{document_type}")
            
            if compliance_flags:
                await memory_store.increment_counter("compliance_flags_detected")
            
            if invoice_total and invoice_total > self.invoice_threshold:
                await memory_store.increment_counter("high_value_invoices")
            
            logger.info(f"PDF processed: {document_type}, {len(compliance_flags)} compliance flags, "
                       f"invoice total: {invoice_total}")
            
            return analysis, actions
            
        except Exception as e:
            logger.error(f"PDF processing failed: {e}")
            raise
    
    async def _extract_pdf_text(self, pdf_content: Union[bytes, io.BytesIO]) -> str:
        """Extract text content from PDF."""
        try:
            if isinstance(pdf_content, bytes):
                pdf_file = io.BytesIO(pdf_content)
            else:
                pdf_file = pdf_content
            
            reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            
            for page_num, page in enumerate(reader.pages):
                try:
                    page_text = page.extract_text()
                    text += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
                except Exception as e:
                    logger.warning(f"Failed to extract text from page {page_num + 1}: {e}")
                    continue
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"Failed to extract PDF text: {e}")
            return ""
    
    async def _classify_document_type(self, text: str) -> str:
        """Classify the type of document based on content."""
        text_lower = text.lower()
        type_scores = {}
        
        for doc_type, keywords in self.document_patterns.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            type_scores[doc_type] = score
        
        # Return the type with highest score, or "unknown" if no clear match
        if type_scores and max(type_scores.values()) > 0:
            return max(type_scores, key=type_scores.get)
        
        return "unknown"
    
    async def _extract_structured_data(self, text: str, document_type: str) -> Dict[str, Any]:
        """Extract structured data based on document type."""
        structured_data = {}
        
        if document_type == "invoice":
            structured_data.update(await self._extract_invoice_fields(text))
        elif document_type == "contract":
            structured_data.update(await self._extract_contract_fields(text))
        elif document_type == "policy":
            structured_data.update(await self._extract_policy_fields(text))
        
        # Common fields for all documents
        structured_data.update(await self._extract_common_fields(text))
        
        return structured_data
    
    async def _extract_invoice_fields(self, text: str) -> Dict[str, Any]:
        """Extract invoice-specific fields."""
        fields = {}
        
        for field_name, pattern in self.invoice_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                if field_name in ["total_amount", "tax", "subtotal"]:
                    # Convert to float, removing commas
                    try:
                        fields[field_name] = float(matches[0].replace(",", ""))
                    except (ValueError, IndexError):
                        fields[field_name] = matches[0]
                else:
                    fields[field_name] = matches[0]
        
        return fields
    
    async def _extract_contract_fields(self, text: str) -> Dict[str, Any]:
        """Extract contract-specific fields."""
        fields = {}
        
        # Extract parties
        party_pattern = r"(?:party|between|by and between)[\s\n]*([A-Z][^,\n]+)"
        parties = re.findall(party_pattern, text, re.IGNORECASE)
        if parties:
            fields["parties"] = parties[:2]  # Usually two main parties
        
        # Extract effective date
        date_pattern = r"(?:effective|dated|date)[\s:]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})"
        dates = re.findall(date_pattern, text, re.IGNORECASE)
        if dates:
            fields["effective_date"] = dates[0]
        
        # Extract term/duration
        term_pattern = r"(?:term|duration|period)[\s:]*(\d+\s*(?:year|month|day)s?)"
        terms = re.findall(term_pattern, text, re.IGNORECASE)
        if terms:
            fields["term"] = terms[0]
        
        return fields
    
    async def _extract_policy_fields(self, text: str) -> Dict[str, Any]:
        """Extract policy-specific fields."""
        fields = {}
        
        # Extract policy number/version
        policy_pattern = r"(?:policy|version|revision)[\s#:]*([A-Z0-9.-]+)"
        policies = re.findall(policy_pattern, text, re.IGNORECASE)
        if policies:
            fields["policy_number"] = policies[0]
        
        # Extract effective date
        date_pattern = r"(?:effective|revised|updated)[\s:]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})"
        dates = re.findall(date_pattern, text, re.IGNORECASE)
        if dates:
            fields["effective_date"] = dates[0]
        
        return fields
    
    async def _extract_common_fields(self, text: str) -> Dict[str, Any]:
        """Extract common fields present in most documents."""
        fields = {}
        
        # Extract emails
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        if emails:
            fields["emails"] = list(set(emails))  # Remove duplicates
        
        # Extract phone numbers
        phone_pattern = r'\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b'
        phones = re.findall(phone_pattern, text)
        if phones:
            fields["phone_numbers"] = [f"({p[0]}) {p[1]}-{p[2]}" for p in phones]
        
        # Extract monetary amounts
        amount_pattern = r'\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
        amounts = re.findall(amount_pattern, text)
        if amounts:
            try:
                fields["monetary_amounts"] = [float(amt.replace(",", "")) for amt in amounts]
            except ValueError:
                fields["monetary_amounts"] = amounts
        
        return fields
    
    async def _check_compliance(self, text: str) -> List[str]:
        """Check for compliance-related keywords and flags."""
        text_lower = text.lower()
        compliance_flags = []
        
        for regulation, keywords in self.compliance_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                compliance_flags.append(regulation)
        
        return compliance_flags
    
    async def _detect_risk_indicators(self, text: str, structured_data: Dict[str, Any]) -> List[str]:
        """Detect risk indicators in the document."""
        risk_indicators = []
        text_lower = text.lower()
        
        # Financial risk indicators
        high_risk_financial = [
            "bankruptcy", "default", "liquidation", "insolvency",
            "financial distress", "going concern", "material weakness"
        ]
        
        if any(indicator in text_lower for indicator in high_risk_financial):
            risk_indicators.append("financial_risk")
        
        # Legal risk indicators
        legal_risk = [
            "lawsuit", "litigation", "legal action", "court order",
            "injunction", "penalty", "fine", "violation"
        ]
        
        if any(indicator in text_lower for indicator in legal_risk):
            risk_indicators.append("legal_risk")
        
        # Data security risk indicators
        security_risk = [
            "data breach", "security incident", "unauthorized access",
            "cyber attack", "malware", "ransomware", "phishing"
        ]
        
        if any(indicator in text_lower for indicator in security_risk):
            risk_indicators.append("security_risk")
        
        # Check for unusually high amounts
        if "monetary_amounts" in structured_data:
            max_amount = max(structured_data["monetary_amounts"], default=0)
            if max_amount > 100000:  # $100,000 threshold
                risk_indicators.append("high_value_transaction")
        
        return risk_indicators
    
    async def _process_invoice_data(self, text: str) -> Tuple[Optional[float], List[Dict[str, Any]]]:
        """Process invoice-specific data extraction."""
        invoice_total = None
        line_items = []
        
        # Extract total amount
        total_pattern = r"(?:total|amount due|grand total)[\s:$]*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)"
        total_matches = re.findall(total_pattern, text, re.IGNORECASE)
        
        if total_matches:
            try:
                invoice_total = float(total_matches[-1].replace(",", ""))  # Take the last match
            except ValueError:
                pass
        
        # Extract line items (simplified pattern)
        line_pattern = r"(\d+(?:\.\d{2})?)\s+([^\n\r$]+?)\s+(\d+(?:\.\d{2})?)"
        line_matches = re.findall(line_pattern, text)
        
        for match in line_matches[:20]:  # Limit to 20 line items
            try:
                quantity = float(match[0])
                description = match[1].strip()
                unit_price = float(match[2])
                
                line_items.append({
                    "quantity": quantity,
                    "description": description,
                    "unit_price": unit_price,
                    "total": quantity * unit_price
                })
            except (ValueError, IndexError):
                continue
        
        return invoice_total, line_items
    
    async def _generate_actions(self, analysis: PDFAnalysis) -> List[ActionRequest]:
        """Generate actions based on PDF analysis."""
        actions = []
        
        # Check for compliance alerts
        if analysis.compliance_flags:
            compliance_action = ActionRequest(
                action_type=ActionType.COMPLIANCE_ALERT,
                payload={
                    "compliance_type": "document_compliance",
                    "regulations": analysis.compliance_flags,
                    "document_info": {
                        "document_type": analysis.document_type,
                        "structured_data": analysis.structured_data
                    },
                    "flagged_keywords": analysis.compliance_flags
                },
                priority=UrgencyLevel.HIGH,
                source_agent=self.name,
                correlation_id=f"pdf_compliance_{hash(analysis.extracted_text)}_{int(datetime.utcnow().timestamp())}"
            )
            actions.append(compliance_action)
        
        # Check for high-value invoices
        if analysis.invoice_total and analysis.invoice_total > self.invoice_threshold:
            high_value_action = ActionRequest(
                action_type=ActionType.FLAG_ANOMALY,
                payload={
                    "anomaly_type": "high_value_invoice",
                    "details": {
                        "invoice_total": analysis.invoice_total,
                        "threshold": self.invoice_threshold,
                        "line_items_count": len(analysis.line_items)
                    },
                    "document_type": analysis.document_type
                },
                priority=UrgencyLevel.HIGH,
                source_agent=self.name,
                correlation_id=f"pdf_high_value_{int(analysis.invoice_total)}_{int(datetime.utcnow().timestamp())}"
            )
            actions.append(high_value_action)
        
        # Check for risk indicators
        if analysis.risk_indicators:
            risk_action = ActionRequest(
                action_type=ActionType.RISK_ALERT,
                payload={
                    "risk_type": "document_risk",
                    "risk_score": min(len(analysis.risk_indicators) * 0.3, 1.0),
                    "risk_indicators": analysis.risk_indicators,
                    "affected_entities": analysis.structured_data.get("emails", []),
                    "document_context": {
                        "document_type": analysis.document_type,
                        "compliance_flags": analysis.compliance_flags
                    }
                },
                priority=UrgencyLevel.HIGH,
                source_agent=self.name,
                correlation_id=f"pdf_risk_{hash(str(analysis.risk_indicators))}_{int(datetime.utcnow().timestamp())}"
            )
            actions.append(risk_action)
        
        return actions


# Global PDF agent instance
pdf_agent = PDFAgent()


async def get_pdf_agent() -> PDFAgent:
    """Get the global PDF agent instance."""
    return pdf_agent
