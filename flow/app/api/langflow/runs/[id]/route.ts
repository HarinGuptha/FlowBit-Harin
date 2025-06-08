import { NextRequest, NextResponse } from 'next/server';

// Mock detailed run data
const mockRunDetails: Record<string, any> = {
  'run_001': {
    id: 'run_001',
    flow_name: 'Email Agent',
    status: 'completed',
    duration: 2340,
    created_at: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
    completed_at: new Date(Date.now() - 1000 * 60 * 3).toISOString(),
    input_data: {
      content: `From: sarah.johnson@email.com
To: support@company.com
Subject: URGENT - Defective Product Complaint - Order #12345
Date: Mon, 6 Jan 2025 14:30:00 +0000

I am EXTREMELY disappointed and frustrated with the product I received!

The laptop I ordered (Order #12345) arrived with a cracked screen and won't even turn on. This is completely unacceptable for a $1,200 purchase. I've been a loyal customer for 3 years, and this is the worst experience I've ever had.

I need this resolved IMMEDIATELY as I need the laptop for work. I expect:
1. A full refund OR immediate replacement
2. Compensation for the inconvenience
3. An explanation of how this happened

If this isn't resolved within 24 hours, I will be filing a complaint with the Better Business Bureau and posting negative reviews everywhere.

This is absolutely ridiculous!

Sarah Johnson
Customer ID: CUST_789456`
    },
    output_data: {
      classification: {
        format_type: 'email',
        business_intent: 'complaint',
        confidence: 0.94,
        reasoning: 'Strong complaint indicators: angry tone, defective product, demands for resolution'
      },
      email_analysis: {
        sender: 'sarah.johnson@email.com',
        subject: 'URGENT - Defective Product Complaint - Order #12345',
        tone: 'angry',
        sentiment_score: -0.87,
        urgency_level: 'critical',
        escalation_required: true,
        key_issues: ['defective_product', 'cracked_screen', 'non_functional', 'refund_demand'],
        customer_info: {
          customer_id: 'CUST_789456',
          order_id: '12345',
          loyalty_status: '3_year_customer',
          purchase_amount: '$1,200'
        }
      },
      actions_triggered: [
        {
          action_type: 'escalate_to_manager',
          priority: 'critical',
          ticket_id: 'ESC-2025-001',
          reason: 'High-value customer with defective product and threat of BBB complaint',
          sla_target: '2_hours'
        },
        {
          action_type: 'crm_update',
          priority: 'high',
          customer_id: 'CUST_789456',
          flag: 'urgent_resolution_required'
        },
        {
          action_type: 'quality_alert',
          priority: 'medium',
          product_sku: 'LAPTOP_MODEL_X',
          issue: 'shipping_damage_pattern'
        }
      ]
    },
    node_details: [
      {
        node_id: 'input-1',
        node_name: 'Email Input',
        status: 'completed',
        duration: 45,
        input: { content: 'Email content...' },
        output: { processed: true }
      },
      {
        node_id: 'parser-1',
        node_name: 'Email Parser',
        status: 'completed',
        duration: 890,
        input: { email_content: 'Email content...' },
        output: { sender: 'angry.customer@email.com', subject: 'URGENT - Defective Product' }
      },
      {
        node_id: 'analyzer-1',
        node_name: 'Tone Analyzer',
        status: 'completed',
        duration: 1200,
        input: { email_content: 'Email content...' },
        output: { tone: 'angry', sentiment_score: -0.85 }
      },
      {
        node_id: 'output-1',
        node_name: 'Email Analysis Output',
        status: 'completed',
        duration: 205,
        input: { combined_results: '...' },
        output: { final_result: 'Complete analysis' }
      }
    ],
    logs: [
      {
        timestamp: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
        level: 'info',
        message: '🚀 Starting email processing workflow for angry customer complaint',
        node_id: 'input-1'
      },
      {
        timestamp: new Date(Date.now() - 1000 * 60 * 4.8).toISOString(),
        level: 'info',
        message: '📧 Email content received - Subject: URGENT - Defective Product Complaint',
        node_id: 'input-1'
      },
      {
        timestamp: new Date(Date.now() - 1000 * 60 * 4.7).toISOString(),
        level: 'info',
        message: '🔍 Parsing email structure and extracting metadata...',
        node_id: 'parser-1'
      },
      {
        timestamp: new Date(Date.now() - 1000 * 60 * 4.5).toISOString(),
        level: 'info',
        message: '✅ Email parsed - Sender: sarah.johnson@email.com, Customer: CUST_789456, Order: #12345',
        node_id: 'parser-1'
      },
      {
        timestamp: new Date(Date.now() - 1000 * 60 * 4.3).toISOString(),
        level: 'info',
        message: '🧠 Analyzing tone, sentiment, and urgency indicators...',
        node_id: 'analyzer-1'
      },
      {
        timestamp: new Date(Date.now() - 1000 * 60 * 4.0).toISOString(),
        level: 'warning',
        message: '🚨 CRITICAL: Angry tone detected with BBB threat - immediate escalation required',
        node_id: 'analyzer-1'
      },
      {
        timestamp: new Date(Date.now() - 1000 * 60 * 3.8).toISOString(),
        level: 'warning',
        message: '📊 Sentiment analysis: -0.87 (highly negative), Urgency: CRITICAL, 3-year loyal customer',
        node_id: 'analyzer-1'
      },
      {
        timestamp: new Date(Date.now() - 1000 * 60 * 3.5).toISOString(),
        level: 'info',
        message: '⚡ Action Router: Triggering multiple escalation actions...',
        node_id: 'action-router-1'
      },
      {
        timestamp: new Date(Date.now() - 1000 * 60 * 3.2).toISOString(),
        level: 'success',
        message: '🎫 Escalation ticket created: ESC-2025-001 (Priority: CRITICAL, SLA: 2 hours)',
        node_id: 'action-router-1'
      },
      {
        timestamp: new Date(Date.now() - 1000 * 60 * 3.0).toISOString(),
        level: 'success',
        message: '📋 CRM updated for CUST_789456 with urgent resolution flag',
        node_id: 'action-router-1'
      },
      {
        timestamp: new Date(Date.now() - 1000 * 60 * 2.8).toISOString(),
        level: 'info',
        message: '🔔 Quality alert sent for LAPTOP_MODEL_X shipping damage pattern',
        node_id: 'action-router-1'
      },
      {
        timestamp: new Date(Date.now() - 1000 * 60 * 2.5).toISOString(),
        level: 'success',
        message: '✨ Email processing completed - 3 actions triggered, manager notified',
        node_id: 'output-1'
      }
    ]
  },
  'run_002': {
    id: 'run_002',
    flow_name: 'JSON Agent',
    status: 'completed',
    duration: 1890,
    created_at: new Date(Date.now() - 1000 * 60 * 15).toISOString(),
    completed_at: new Date(Date.now() - 1000 * 60 * 13).toISOString(),
    input_data: {
      content: '{"event_type": "payment", "amount": 999999.99, "user_id": "test123"}'
    },
    output_data: {
      validation: {
        is_valid_json: true,
        schema_type: 'webhook',
        confidence: 0.88
      },
      anomaly_analysis: {
        anomaly_score: 0.95,
        risk_level: 'critical',
        detected_anomalies: ['unusual_amount', 'suspicious_pattern']
      },
      recommended_actions: [
        {
          action_type: 'flag',
          priority: 'critical',
          reason: 'Extremely high transaction amount detected'
        }
      ]
    },
    node_details: [
      {
        node_id: 'input-1',
        node_name: 'JSON Input',
        status: 'completed',
        duration: 32,
        input: { content: 'JSON data...' },
        output: { validated: true }
      },
      {
        node_id: 'validator-1',
        node_name: 'JSON Validator',
        status: 'completed',
        duration: 567,
        input: { json_data: 'JSON data...' },
        output: { is_valid: true, schema_type: 'webhook' }
      },
      {
        node_id: 'anomaly-detector-1',
        node_name: 'Anomaly Detector',
        status: 'completed',
        duration: 1123,
        input: { json_data: 'JSON data...' },
        output: { anomaly_score: 0.95, risk_level: 'critical' }
      },
      {
        node_id: 'output-1',
        node_name: 'JSON Analysis Output',
        status: 'completed',
        duration: 168,
        input: { combined_results: '...' },
        output: { final_analysis: 'Complete' }
      }
    ],
    logs: [
      {
        timestamp: new Date(Date.now() - 1000 * 60 * 15).toISOString(),
        level: 'info',
        message: 'Starting JSON validation and analysis',
        node_id: 'input-1'
      },
      {
        timestamp: new Date(Date.now() - 1000 * 60 * 14.8).toISOString(),
        level: 'info',
        message: 'JSON syntax validation passed',
        node_id: 'validator-1'
      },
      {
        timestamp: new Date(Date.now() - 1000 * 60 * 14.5).toISOString(),
        level: 'info',
        message: 'Schema identified as webhook type',
        node_id: 'validator-1'
      },
      {
        timestamp: new Date(Date.now() - 1000 * 60 * 14.2).toISOString(),
        level: 'info',
        message: 'Running anomaly detection algorithms...',
        node_id: 'anomaly-detector-1'
      },
      {
        timestamp: new Date(Date.now() - 1000 * 60 * 13.8).toISOString(),
        level: 'error',
        message: 'CRITICAL: Extremely high amount detected - $999,999.99',
        node_id: 'anomaly-detector-1'
      },
      {
        timestamp: new Date(Date.now() - 1000 * 60 * 13.5).toISOString(),
        level: 'warning',
        message: 'Anomaly score: 0.95 - flagging for review',
        node_id: 'anomaly-detector-1'
      },
      {
        timestamp: new Date(Date.now() - 1000 * 60 * 13.0).toISOString(),
        level: 'success',
        message: 'JSON analysis completed - high-risk transaction flagged',
        node_id: 'output-1'
      }
    ]
  }
};

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const runId = params.id;
    
    // In production, this would call the actual LangFlow API
    const langflowUrl = process.env.LANGFLOW_BASE_URL || 'http://localhost:7860';
    
    // For now, return mock data
    const runDetails = mockRunDetails[runId];
    
    if (!runDetails) {
      return NextResponse.json(
        { error: 'Run not found' },
        { status: 404 }
      );
    }

    return NextResponse.json(runDetails);

  } catch (error) {
    console.error('Error fetching LangFlow run details:', error);
    return NextResponse.json(
      { error: 'Failed to fetch run details' },
      { status: 500 }
    );
  }
}
