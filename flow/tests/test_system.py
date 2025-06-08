#!/usr/bin/env python3
"""
FlowBit LangFlow Integration System Tests
Tests all API endpoints and demonstrates functionality
"""

import requests
import json
import time
import sys
from typing import Dict, Any

BASE_URL = "http://localhost:3000"

class FlowBitTester:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
    
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
    
    def test_langflow_runs_api(self):
        """Test GET /api/langflow/runs"""
        try:
            response = self.session.get(f"{self.base_url}/api/langflow/runs")
            success = response.status_code == 200
            data = response.json() if success else {}
            
            details = f"Status: {response.status_code}"
            if success:
                details += f", Runs: {len(data.get('runs', []))}"
            
            self.log_test("LangFlow Runs API", success, details)
            return data
        except Exception as e:
            self.log_test("LangFlow Runs API", False, f"Error: {str(e)}")
            return None
    
    def test_trigger_classifier(self):
        """Test triggering Classifier Agent"""
        payload = {
            "workflowId": "classifier",
            "engine": "langflow",
            "triggerType": "manual",
            "inputPayload": {
                "content": "From: angry@customer.com\nSubject: URGENT COMPLAINT\nI am extremely disappointed with your service!"
            }
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/trigger",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            success = response.status_code == 200
            data = response.json() if success else {}
            
            details = f"Status: {response.status_code}"
            if success:
                details += f", Run ID: {data.get('result', {}).get('run_id', 'N/A')}"
            
            self.log_test("Trigger Classifier Agent", success, details)
            return data
        except Exception as e:
            self.log_test("Trigger Classifier Agent", False, f"Error: {str(e)}")
            return None
    
    def test_trigger_email_agent(self):
        """Test triggering Email Agent"""
        payload = {
            "workflowId": "email",
            "engine": "langflow",
            "triggerType": "manual",
            "inputPayload": {
                "content": "From: support@company.com\nTo: customer@email.com\nSubject: Thank you for your feedback\n\nWe appreciate your input and will address your concerns promptly."
            }
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/trigger",
                json=payload
            )
            success = response.status_code == 200
            data = response.json() if success else {}
            
            details = f"Status: {response.status_code}"
            if success:
                details += f", Run ID: {data.get('result', {}).get('run_id', 'N/A')}"
            
            self.log_test("Trigger Email Agent", success, details)
            return data
        except Exception as e:
            self.log_test("Trigger Email Agent", False, f"Error: {str(e)}")
            return None
    
    def test_webhook_endpoint(self):
        """Test webhook endpoint"""
        payload = {
            "content": "Urgent customer complaint about defective product",
            "priority": "high",
            "customer_id": "CUST_12345"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/hooks/classifier",
                json=payload
            )
            success = response.status_code == 200
            data = response.json() if success else {}
            
            details = f"Status: {response.status_code}"
            if success:
                details += f", Execution ID: {data.get('execution_id', 'N/A')}"
            
            self.log_test("Webhook Endpoint", success, details)
            return data
        except Exception as e:
            self.log_test("Webhook Endpoint", False, f"Error: {str(e)}")
            return None
    
    def test_cron_jobs_api(self):
        """Test cron jobs API"""
        try:
            # Get existing cron jobs
            response = self.session.get(f"{self.base_url}/api/cron")
            success = response.status_code == 200
            data = response.json() if success else {}
            
            details = f"Status: {response.status_code}"
            if success:
                details += f", Jobs: {len(data.get('jobs', []))}"
            
            self.log_test("Cron Jobs API", success, details)
            return data
        except Exception as e:
            self.log_test("Cron Jobs API", False, f"Error: {str(e)}")
            return None
    
    def test_create_cron_job(self):
        """Test creating a cron job"""
        payload = {
            "workflowId": "json",
            "engine": "langflow",
            "schedule": "0 */6 * * *",  # Every 6 hours
            "description": "Automated JSON validation every 6 hours",
            "enabled": True,
            "inputPayload": {
                "content": '{"event": "scheduled_check", "timestamp": "' + str(int(time.time())) + '"}'
            }
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/cron",
                json=payload
            )
            success = response.status_code == 200
            data = response.json() if success else {}
            
            details = f"Status: {response.status_code}"
            if success:
                details += f", Job ID: {data.get('job', {}).get('id', 'N/A')}"
            
            self.log_test("Create Cron Job", success, details)
            return data
        except Exception as e:
            self.log_test("Create Cron Job", False, f"Error: {str(e)}")
            return None
    
    def test_run_details(self, run_id: str = "run_001"):
        """Test getting run details"""
        try:
            response = self.session.get(f"{self.base_url}/api/langflow/runs/{run_id}")
            success = response.status_code == 200
            data = response.json() if success else {}
            
            details = f"Status: {response.status_code}"
            if success:
                details += f", Flow: {data.get('flow_name', 'N/A')}, Status: {data.get('status', 'N/A')}"
            
            self.log_test("Run Details API", success, details)
            return data
        except Exception as e:
            self.log_test("Run Details API", False, f"Error: {str(e)}")
            return None
    
    def run_all_tests(self):
        """Run comprehensive system tests"""
        print("🚀 Starting FlowBit LangFlow Integration Tests")
        print("=" * 60)
        
        # Test 1: LangFlow Runs API
        print("\n📊 Testing LangFlow Runs API...")
        self.test_langflow_runs_api()
        
        # Test 2: Trigger Classifier Agent
        print("\n🤖 Testing Classifier Agent Trigger...")
        self.test_trigger_classifier()
        
        # Test 3: Trigger Email Agent
        print("\n📧 Testing Email Agent Trigger...")
        self.test_trigger_email_agent()
        
        # Test 4: Webhook Endpoint
        print("\n🔗 Testing Webhook Endpoint...")
        self.test_webhook_endpoint()
        
        # Test 5: Cron Jobs API
        print("\n⏰ Testing Cron Jobs API...")
        self.test_cron_jobs_api()
        
        # Test 6: Create Cron Job
        print("\n📅 Testing Cron Job Creation...")
        self.test_create_cron_job()
        
        # Test 7: Run Details
        print("\n📋 Testing Run Details API...")
        self.test_run_details()
        
        # Summary
        print("\n" + "=" * 60)
        print("🎯 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}")
        
        print(f"\n📈 Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🏆 ALL TESTS PASSED! System is working perfectly!")
        else:
            print("⚠️  Some tests failed. Check the details above.")
        
        return passed == total

def main():
    """Main test runner"""
    print("FlowBit LangFlow Integration - System Tests")
    print("Testing against:", BASE_URL)
    print()
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/api/langflow/runs", timeout=5)
        print("✅ Server is running and accessible")
    except Exception as e:
        print(f"❌ Cannot connect to server at {BASE_URL}")
        print(f"   Make sure 'npm run dev' is running")
        print(f"   Error: {str(e)}")
        sys.exit(1)
    
    # Run tests
    tester = FlowBitTester(BASE_URL)
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
