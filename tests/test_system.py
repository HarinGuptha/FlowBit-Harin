"""
Comprehensive test suite for the Multi-Format Autonomous AI System.
Tests all agents, core components, and end-to-end workflows.
"""
import asyncio
import json
import pytest
from datetime import datetime
from typing import Dict, Any

# Import system components
from agents import get_classifier_agent, get_email_agent, get_json_agent, get_pdf_agent
from core import get_memory_store, get_action_router
from models.schemas import FormatType, BusinessIntent, ActionType
from utils.sample_data import SampleDataGenerator


class TestMultiAgentSystem:
    """Comprehensive test suite for the multi-agent system."""
    
    @pytest.fixture(autouse=True)
    async def setup(self):
        """Setup test environment."""
        self.generator = SampleDataGenerator()
        self.memory_store = await get_memory_store()
        self.action_router = await get_action_router()
        
        # Initialize agents
        self.classifier = await get_classifier_agent()
        self.email_agent = await get_email_agent()
        self.json_agent = await get_json_agent()
        self.pdf_agent = await get_pdf_agent()
    
    async def test_classifier_agent(self):
        """Test the classifier agent with various inputs."""
        print("\n=== Testing Classifier Agent ===")
        
        # Test email classification
        email_content = self.generator.generate_sample_email("complaint")
        result = await self.classifier.classify(email_content)
        
        assert result.format_type == FormatType.EMAIL
        assert result.confidence > 0.5
        print(f"✓ Email classified as {result.format_type.value} with confidence {result.confidence:.2f}")
        
        # Test JSON classification
        json_content = json.dumps(self.generator.generate_sample_json("webhook"))
        result = await self.classifier.classify(json_content)
        
        assert result.format_type == FormatType.JSON
        assert result.confidence > 0.5
        print(f"✓ JSON classified as {result.format_type.value} with confidence {result.confidence:.2f}")
        
        # Test PDF classification (simulated)
        pdf_content = self.generator.generate_sample_pdf_content("invoice")
        result = await self.classifier.classify(pdf_content, {"content_type": "application/pdf"})
        
        assert result.format_type == FormatType.PDF
        print(f"✓ PDF classified as {result.format_type.value} with confidence {result.confidence:.2f}")
    
    async def test_email_agent(self):
        """Test the email agent with different email types."""
        print("\n=== Testing Email Agent ===")
        
        # Test complaint email
        complaint_email = self.generator.generate_sample_email("complaint")
        email_data, analysis, actions = await self.email_agent.process_email(complaint_email)
        
        assert email_data.sender
        assert analysis.tone
        assert analysis.urgency
        print(f"✓ Complaint email processed: {analysis.tone.value} tone, {analysis.urgency.value} urgency")
        print(f"  Escalation required: {analysis.requires_escalation}")
        print(f"  Actions generated: {len(actions)}")
        
        # Test RFQ email
        rfq_email = self.generator.generate_sample_email("rfq")
        email_data, analysis, actions = await self.email_agent.process_email(rfq_email)
        
        assert email_data.subject
        print(f"✓ RFQ email processed: {analysis.tone.value} tone, {analysis.urgency.value} urgency")
    
    async def test_json_agent(self):
        """Test the JSON agent with valid and anomalous data."""
        print("\n=== Testing JSON Agent ===")
        
        # Test valid JSON
        valid_json = self.generator.generate_sample_json("webhook")
        result, actions = await self.json_agent.process_json(valid_json, "webhook")
        
        assert result.is_valid
        print(f"✓ Valid JSON processed: valid={result.is_valid}, anomaly_score={result.anomaly_score:.2f}")
        
        # Test anomalous JSON
        anomalous_json = self.generator.generate_anomalous_json()
        result, actions = await self.json_agent.process_json(anomalous_json, "webhook")
        
        print(f"✓ Anomalous JSON processed: valid={result.is_valid}, anomaly_score={result.anomaly_score:.2f}")
        print(f"  Anomalies detected: {result.anomalies}")
        print(f"  Actions generated: {len(actions)}")
        
        # Test invalid JSON
        invalid_json = '{"invalid": json, missing quotes}'
        result, actions = await self.json_agent.process_json(invalid_json, "webhook")
        
        assert not result.is_valid
        print(f"✓ Invalid JSON handled: valid={result.is_valid}, errors={len(result.schema_errors)}")
    
    async def test_pdf_agent(self):
        """Test the PDF agent with different document types."""
        print("\n=== Testing PDF Agent ===")
        
        # Test invoice PDF
        invoice_content = self.generator.generate_sample_pdf_content("invoice")
        analysis, actions = await self.pdf_agent.process_pdf(invoice_content.encode())
        
        assert analysis.document_type
        print(f"✓ Invoice PDF processed: type={analysis.document_type}")
        print(f"  Invoice total: ${analysis.invoice_total}")
        print(f"  Line items: {len(analysis.line_items)}")
        print(f"  Actions generated: {len(actions)}")
        
        # Test compliance document
        policy_content = self.generator.generate_sample_pdf_content("policy")
        analysis, actions = await self.pdf_agent.process_pdf(policy_content.encode())
        
        print(f"✓ Policy PDF processed: type={analysis.document_type}")
        print(f"  Compliance flags: {analysis.compliance_flags}")
        print(f"  Risk indicators: {analysis.risk_indicators}")
    
    async def test_action_router(self):
        """Test the action router with different action types."""
        print("\n=== Testing Action Router ===")
        
        from models.schemas import ActionRequest, UrgencyLevel
        
        # Test escalation action
        escalation_request = ActionRequest(
            action_type=ActionType.ESCALATE,
            payload={
                "description": "Test escalation",
                "customer_info": {"email": "test@example.com"},
                "escalation_reason": "High priority issue"
            },
            priority=UrgencyLevel.HIGH,
            source_agent="test_agent",
            correlation_id="test_123"
        )
        
        result = await self.action_router.route_action(escalation_request)
        assert result.status == "success"
        print(f"✓ Escalation action executed: {result.action_id}")
        
        # Test anomaly flag action
        anomaly_request = ActionRequest(
            action_type=ActionType.FLAG_ANOMALY,
            payload={
                "anomaly_type": "test_anomaly",
                "details": {"test": "data"}
            },
            priority=UrgencyLevel.MEDIUM,
            source_agent="test_agent",
            correlation_id="test_456"
        )
        
        result = await self.action_router.route_action(anomaly_request)
        assert result.status == "success"
        print(f"✓ Anomaly flag action executed: {result.action_id}")
    
    async def test_memory_store(self):
        """Test the shared memory store functionality."""
        print("\n=== Testing Memory Store ===")
        
        from models.schemas import MemoryEntry, ProcessingSession, ClassificationResult
        
        # Test storing and retrieving memory entry
        entry = MemoryEntry(
            key="test_key",
            value={"test": "data"},
            entry_type="test",
            agent_source="test_agent"
        )
        
        success = await self.memory_store.store_entry(entry)
        assert success
        
        retrieved = await self.memory_store.get_entry("test_key")
        assert retrieved is not None
        assert retrieved.value == {"test": "data"}
        print("✓ Memory entry stored and retrieved successfully")
        
        # Test session storage
        classification = ClassificationResult(
            format_type=FormatType.EMAIL,
            business_intent=BusinessIntent.COMPLAINT,
            confidence=0.85
        )
        
        session = ProcessingSession(
            session_id="test_session_123",
            input_metadata={"test": "metadata"},
            classification=classification,
            final_status="completed"
        )
        
        success = await self.memory_store.store_session(session)
        assert success
        
        retrieved_session = await self.memory_store.get_session("test_session_123")
        assert retrieved_session is not None
        assert retrieved_session.session_id == "test_session_123"
        print("✓ Processing session stored and retrieved successfully")
    
    async def test_end_to_end_workflow(self):
        """Test complete end-to-end processing workflow."""
        print("\n=== Testing End-to-End Workflow ===")
        
        # Generate test content
        email_content = self.generator.generate_sample_email("complaint")
        
        # Step 1: Classify
        classification = await self.classifier.classify(email_content)
        print(f"✓ Step 1 - Classification: {classification.format_type.value} + {classification.business_intent.value}")
        
        # Step 2: Process with appropriate agent
        if classification.format_type == FormatType.EMAIL:
            email_data, analysis, actions = await self.email_agent.process_email(email_content)
            print(f"✓ Step 2 - Email processing: {len(actions)} actions generated")
            
            # Step 3: Execute actions
            executed_actions = []
            for action_request in actions:
                result = await self.action_router.route_action(action_request)
                executed_actions.append(result)
            
            print(f"✓ Step 3 - Action execution: {len(executed_actions)} actions executed")
            
            # Step 4: Store session
            session = ProcessingSession(
                session_id=f"e2e_test_{datetime.utcnow().timestamp()}",
                input_metadata={"source": "end_to_end_test"},
                classification=classification,
                actions_triggered=executed_actions,
                final_status="completed"
            )
            
            success = await self.memory_store.store_session(session)
            assert success
            print(f"✓ Step 4 - Session storage: {session.session_id}")
        
        print("✓ End-to-end workflow completed successfully!")
    
    async def test_performance_metrics(self):
        """Test system performance with multiple concurrent requests."""
        print("\n=== Testing Performance Metrics ===")
        
        import time
        
        # Generate multiple test items
        test_emails = [self.generator.generate_sample_email() for _ in range(5)]
        test_jsons = [self.generator.generate_sample_json() for _ in range(5)]
        
        # Test concurrent email processing
        start_time = time.time()
        
        email_tasks = [
            self.email_agent.process_email(email) 
            for email in test_emails
        ]
        
        email_results = await asyncio.gather(*email_tasks)
        email_time = time.time() - start_time
        
        print(f"✓ Processed {len(test_emails)} emails in {email_time:.2f}s")
        print(f"  Average time per email: {email_time/len(test_emails):.3f}s")
        
        # Test concurrent JSON processing
        start_time = time.time()
        
        json_tasks = [
            self.json_agent.process_json(json_data)
            for json_data in test_jsons
        ]
        
        json_results = await asyncio.gather(*json_tasks)
        json_time = time.time() - start_time
        
        print(f"✓ Processed {len(test_jsons)} JSON objects in {json_time:.2f}s")
        print(f"  Average time per JSON: {json_time/len(test_jsons):.3f}s")
        
        # Test memory store performance
        start_time = time.time()
        counter_tasks = [
            self.memory_store.increment_counter(f"test_counter_{i}")
            for i in range(10)
        ]
        
        await asyncio.gather(*counter_tasks)
        memory_time = time.time() - start_time
        
        print(f"✓ Executed {len(counter_tasks)} memory operations in {memory_time:.3f}s")


async def run_tests():
    """Run all tests."""
    print("🚀 Starting Multi-Agent System Test Suite")
    print("=" * 50)
    
    test_suite = TestMultiAgentSystem()
    await test_suite.setup()
    
    try:
        await test_suite.test_classifier_agent()
        await test_suite.test_email_agent()
        await test_suite.test_json_agent()
        await test_suite.test_pdf_agent()
        await test_suite.test_action_router()
        await test_suite.test_memory_store()
        await test_suite.test_end_to_end_workflow()
        await test_suite.test_performance_metrics()
        
        print("\n" + "=" * 50)
        print("🎉 All tests completed successfully!")
        print("✅ Multi-Agent System is functioning correctly")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise
    
    finally:
        # Cleanup
        await test_suite.memory_store.disconnect()


if __name__ == "__main__":
    asyncio.run(run_tests())
