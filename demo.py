"""
Demo script for the Multi-Format Autonomous AI System.
Showcases all features with realistic examples and detailed output.
"""
import asyncio
import json
import time
from datetime import datetime
from typing import Dict, Any

# Import system components
from agents import get_classifier_agent, get_email_agent, get_json_agent, get_pdf_agent
from core import get_memory_store, get_action_router
from utils.sample_data import SampleDataGenerator


class SystemDemo:
    """Interactive demo of the multi-agent system."""
    
    def __init__(self):
        self.generator = SampleDataGenerator()
        
    async def initialize(self):
        """Initialize all system components."""
        print("🚀 Initializing Multi-Format Autonomous AI System...")
        print("=" * 60)
        
        # Initialize core components
        self.memory_store = await get_memory_store()
        self.action_router = await get_action_router()
        
        # Initialize agents
        self.classifier = await get_classifier_agent()
        self.email_agent = await get_email_agent()
        self.json_agent = await get_json_agent()
        self.pdf_agent = await get_pdf_agent()
        
        print("✅ All components initialized successfully!")
        print()
    
    def print_section(self, title: str):
        """Print a formatted section header."""
        print(f"\n{'='*60}")
        print(f"🎯 {title}")
        print(f"{'='*60}")
    
    def print_subsection(self, title: str):
        """Print a formatted subsection header."""
        print(f"\n📋 {title}")
        print("-" * 40)
    
    async def demo_email_processing(self):
        """Demonstrate email processing capabilities."""
        self.print_section("EMAIL PROCESSING DEMONSTRATION")
        
        # Demo 1: Angry Customer Complaint
        self.print_subsection("Scenario 1: Angry Customer Complaint")
        
        angry_email = """From: frustrated.customer@email.com
To: support@company.com
Subject: URGENT - Defective Product - DEMAND REFUND
Date: Mon, 15 Jan 2024 14:30:00 +0000

I am absolutely FURIOUS about the defective product I received last week!

This is completely UNACCEPTABLE. The item was broken when it arrived, 
and your customer service has been useless. I've been a loyal customer 
for 5 years and this is how you treat me?

I DEMAND an immediate full refund or I will:
1. Contact my lawyer
2. Report you to the Better Business Bureau  
3. Post negative reviews everywhere
4. Dispute the charge with my credit card company

Order ID: ORD-2024-12345
Amount: $299.99
Phone: (555) 123-4567

This needs to be resolved TODAY or you'll be hearing from my attorney!

Extremely disappointed,
Sarah Johnson
sarah.johnson@email.com"""

        print("📧 Processing angry customer email...")
        
        # Step 1: Classification
        start_time = time.time()
        classification = await self.classifier.classify(angry_email)
        classification_time = (time.time() - start_time) * 1000
        
        print(f"✅ Classification completed in {classification_time:.1f}ms")
        print(f"   Format: {classification.format_type.value}")
        print(f"   Intent: {classification.business_intent.value}")
        print(f"   Confidence: {classification.confidence:.2f}")
        
        # Step 2: Email Processing
        start_time = time.time()
        email_data, analysis, actions = await self.email_agent.process_email(angry_email)
        processing_time = (time.time() - start_time) * 1000
        
        print(f"\n✅ Email analysis completed in {processing_time:.1f}ms")
        print(f"   Sender: {email_data.sender}")
        print(f"   Subject: {email_data.subject}")
        print(f"   Tone: {analysis.tone.value}")
        print(f"   Urgency: {analysis.urgency.value}")
        print(f"   Sentiment Score: {analysis.sentiment_score:.2f}")
        print(f"   Requires Escalation: {analysis.requires_escalation}")
        print(f"   Key Phrases: {', '.join(analysis.key_phrases[:3])}")
        
        # Step 3: Action Execution
        print(f"\n🔄 Executing {len(actions)} actions...")
        executed_actions = []
        
        for i, action_request in enumerate(actions, 1):
            start_time = time.time()
            result = await self.action_router.route_action(action_request)
            execution_time = (time.time() - start_time) * 1000
            
            executed_actions.append(result)
            print(f"   Action {i}: {action_request.action_type.value} - {result.status} ({execution_time:.1f}ms)")
            
            if result.response_data:
                if "crm_response" in result.response_data:
                    ticket_id = result.response_data["crm_response"]["ticket_id"]
                    print(f"      → Escalation ticket created: {ticket_id}")
        
        # Demo 2: Polite RFQ
        self.print_subsection("Scenario 2: Polite RFQ Request")
        
        rfq_email = self.generator.generate_sample_email("rfq")
        print("📧 Processing RFQ email...")
        
        classification = await self.classifier.classify(rfq_email)
        email_data, analysis, actions = await self.email_agent.process_email(rfq_email)
        
        print(f"✅ RFQ processed: {analysis.tone.value} tone, {analysis.urgency.value} urgency")
        print(f"   Actions: {len(actions)} (routine processing)")
    
    async def demo_json_processing(self):
        """Demonstrate JSON processing and anomaly detection."""
        self.print_section("JSON PROCESSING & ANOMALY DETECTION")
        
        # Demo 1: Valid Webhook
        self.print_subsection("Scenario 1: Valid Webhook Data")
        
        valid_webhook = {
            "event_type": "payment_completed",
            "timestamp": "2024-01-15T14:30:00Z",
            "data": {
                "user_id": "user_12345",
                "amount": 149.99,
                "currency": "USD",
                "transaction_id": "txn_abc123def456"
            },
            "metadata": {
                "source": "payment_gateway",
                "version": "2.1",
                "ip_address": "192.168.1.100"
            }
        }
        
        print("📊 Processing valid webhook...")
        result, actions = await self.json_agent.process_json(valid_webhook, "webhook")
        
        print(f"✅ Validation: {result.is_valid}")
        print(f"   Anomaly Score: {result.anomaly_score:.2f}")
        print(f"   Schema Errors: {len(result.schema_errors)}")
        print(f"   Actions Generated: {len(actions)}")
        
        # Demo 2: Anomalous Data
        self.print_subsection("Scenario 2: Suspicious Transaction")
        
        suspicious_data = {
            "event_type": "payment_completed",
            "timestamp": "2024-01-15T14:30:00Z",
            "data": {
                "user_id": "user_12345",
                "amount": 999999.99,  # Suspiciously high amount
                "currency": "USD",
                "transaction_id": "txn_abc123def456",
                "description": "<script>alert('xss')</script>",  # Malicious content
                "notes": "'; DROP TABLE users; --"  # SQL injection attempt
            }
        }
        
        print("🚨 Processing suspicious transaction...")
        result, actions = await self.json_agent.process_json(suspicious_data, "webhook")
        
        print(f"⚠️  Validation: {result.is_valid}")
        print(f"   Anomaly Score: {result.anomaly_score:.2f}")
        print(f"   Anomalies Detected: {', '.join(result.anomalies)}")
        print(f"   Actions Generated: {len(actions)}")
        
        # Execute high-priority actions
        if actions:
            print("\n🔄 Executing security actions...")
            for action_request in actions:
                result = await self.action_router.route_action(action_request)
                if action_request.action_type.value == "risk_alert":
                    alert_id = result.response_data["risk_alert"]["alert_id"]
                    print(f"   → Risk alert created: {alert_id}")
    
    async def demo_pdf_processing(self):
        """Demonstrate PDF processing and compliance checking."""
        self.print_section("PDF PROCESSING & COMPLIANCE CHECKING")
        
        # Demo 1: High-Value Invoice
        self.print_subsection("Scenario 1: High-Value Invoice")
        
        invoice_content = """
INVOICE

Invoice Number: INV-2024-15678
Date: January 15, 2024
Due Date: February 14, 2024

Bill To:
Acme Corporation
John Smith, CFO
123 Business Ave
New York, NY 10001
john.smith@acme.com

Line Items:
1. Enterprise Software License - Qty: 50 @ $299.99 = $14,999.50
2. Professional Services - Qty: 40 @ $150.00 = $6,000.00
3. Training and Support - Qty: 1 @ $2,500.00 = $2,500.00

Subtotal: $23,499.50
Tax (8.5%): $1,997.46
Total Amount Due: $25,496.96

Payment Terms: Net 30 days
Thank you for your business!
"""
        
        print("📄 Processing high-value invoice...")
        analysis, actions = await self.pdf_agent.process_pdf(invoice_content.encode())
        
        print(f"✅ Document Type: {analysis.document_type}")
        print(f"   Invoice Total: ${analysis.invoice_total:,.2f}")
        print(f"   Line Items: {len(analysis.line_items)}")
        print(f"   Risk Indicators: {analysis.risk_indicators}")
        print(f"   Actions Generated: {len(actions)}")
        
        if analysis.invoice_total and analysis.invoice_total > 10000:
            print(f"   🚨 High-value invoice flagged (>${analysis.invoice_total:,.2f})")
        
        # Demo 2: GDPR Compliance Document
        self.print_subsection("Scenario 2: GDPR Compliance Policy")
        
        gdpr_policy = """
GDPR COMPLIANCE POLICY

Policy Number: POL-2024-GDPR-001
Effective Date: January 1, 2024
Last Revised: January 15, 2024

1. PURPOSE
This policy establishes guidelines for GDPR compliance within our organization
to protect personal data and ensure data subject rights.

2. SCOPE
This policy applies to all employees, contractors, and third parties who handle
personal data of EU residents.

3. DATA PROTECTION REQUIREMENTS
- All personal data must be processed lawfully and transparently
- Data subjects have the right to be forgotten
- Consent must be obtained for data processing
- Data protection by design must be implemented
- Regular audits must be conducted to ensure compliance

4. DATA BREACH PROCEDURES
Any suspected data breach must be reported to the Data Protection Officer
within 24 hours of discovery.

5. VIOLATIONS
Failure to comply with GDPR requirements may result in fines up to 4% of
annual global turnover or €20 million, whichever is higher.

Approved by: Jane Doe, Chief Privacy Officer
Date: January 15, 2024
"""
        
        print("📋 Processing GDPR compliance document...")
        analysis, actions = await self.pdf_agent.process_pdf(gdpr_policy.encode())
        
        print(f"✅ Document Type: {analysis.document_type}")
        print(f"   Compliance Flags: {', '.join(analysis.compliance_flags)}")
        print(f"   Risk Indicators: {analysis.risk_indicators}")
        print(f"   Actions Generated: {len(actions)}")
        
        if actions:
            print("\n🔄 Executing compliance actions...")
            for action_request in actions:
                result = await self.action_router.route_action(action_request)
                if action_request.action_type.value == "compliance_alert":
                    alert_id = result.response_data["compliance_alert"]["alert_id"]
                    print(f"   → Compliance alert created: {alert_id}")
    
    async def demo_system_integration(self):
        """Demonstrate complete system integration and chaining."""
        self.print_section("SYSTEM INTEGRATION & ACTION CHAINING")
        
        print("🔗 Demonstrating end-to-end processing with action chaining...")
        
        # Process multiple inputs simultaneously
        test_inputs = [
            ("Email", self.generator.generate_sample_email("complaint")),
            ("JSON", json.dumps(self.generator.generate_anomalous_json())),
            ("PDF", self.generator.generate_sample_pdf_content("policy"))
        ]
        
        total_actions = 0
        processing_times = []
        
        for input_type, content in test_inputs:
            print(f"\n📥 Processing {input_type} input...")
            
            start_time = time.time()
            
            # Step 1: Classify
            classification = await self.classifier.classify(content)
            
            # Step 2: Route to appropriate agent
            actions = []
            if classification.format_type.value == "email":
                _, _, actions = await self.email_agent.process_email(content)
            elif classification.format_type.value == "json":
                _, actions = await self.json_agent.process_json(json.loads(content))
            elif classification.format_type.value == "pdf":
                _, actions = await self.pdf_agent.process_pdf(content.encode())
            
            # Step 3: Execute actions
            for action_request in actions:
                await self.action_router.route_action(action_request)
            
            processing_time = (time.time() - start_time) * 1000
            processing_times.append(processing_time)
            total_actions += len(actions)
            
            print(f"   ✅ {input_type}: {len(actions)} actions in {processing_time:.1f}ms")
        
        print(f"\n📊 Integration Summary:")
        print(f"   Total Actions Executed: {total_actions}")
        print(f"   Average Processing Time: {sum(processing_times)/len(processing_times):.1f}ms")
        print(f"   System Throughput: {len(test_inputs)/(sum(processing_times)/1000):.1f} items/second")
    
    async def demo_system_monitoring(self):
        """Demonstrate system monitoring and analytics."""
        self.print_section("SYSTEM MONITORING & ANALYTICS")
        
        print("📈 Retrieving system statistics...")
        
        # Get system stats
        stats = await self.memory_store.get_system_stats()
        action_stats = await self.action_router.get_action_statistics()
        
        print(f"\n📊 Processing Statistics:")
        print(f"   Total Sessions: {stats.get('total_sessions', 0)}")
        print(f"   Actions Executed: {action_stats.get('total_actions_executed', 0)}")
        print(f"   Success Rate: {action_stats.get('success_rate', 0):.1f}%")
        
        print(f"\n🔍 Memory Store Status:")
        print(f"   Connected: {stats.get('connected', False)}")
        print(f"   Memory Usage: {stats.get('memory_usage', 0)} bytes")
        
        print(f"\n⚡ Performance Counters:")
        counters = stats.get('counters', {})
        for counter_name, count in counters.items():
            if count > 0:
                print(f"   {counter_name}: {count}")
    
    async def run_complete_demo(self):
        """Run the complete system demonstration."""
        await self.initialize()
        
        try:
            await self.demo_email_processing()
            await self.demo_json_processing()
            await self.demo_pdf_processing()
            await self.demo_system_integration()
            await self.demo_system_monitoring()
            
            self.print_section("DEMO COMPLETED SUCCESSFULLY! 🎉")
            print("✅ All system components functioning correctly")
            print("✅ Multi-agent coordination working seamlessly")
            print("✅ Action chaining and routing operational")
            print("✅ Memory store and analytics active")
            print("\n🌟 The Multi-Format Autonomous AI System is ready for production!")
            
        except Exception as e:
            print(f"\n❌ Demo failed: {e}")
            raise
        
        finally:
            await self.memory_store.disconnect()


async def main():
    """Main demo entry point."""
    print("🤖 Multi-Format Autonomous AI System")
    print("🎯 Contextual Decisioning & Chained Actions")
    print("🏆 Flowbit AI Assessment Demo")
    print()
    
    demo = SystemDemo()
    await demo.run_complete_demo()


if __name__ == "__main__":
    asyncio.run(main())
