import { NextRequest, NextResponse } from 'next/server';

// Store for webhook executions (in production, use a proper database)
const webhookExecutions: Record<string, any[]> = {};

export async function GET(
  request: NextRequest,
  { params }: { params: { workflowId: string } }
) {
  try {
    const workflowId = params.workflowId;
    
    return NextResponse.json({
      webhook_url: `${process.env.NEXT_PUBLIC_BASE_URL || 'http://localhost:3000'}/api/hooks/${workflowId}`,
      workflow_id: workflowId,
      method: 'POST',
      content_type: 'application/json',
      description: 'Public webhook endpoint for triggering LangFlow workflows',
      recent_executions: webhookExecutions[workflowId]?.slice(-10) || []
    });
  } catch (error) {
    console.error('Error getting webhook info:', error);
    return NextResponse.json(
      { error: 'Failed to get webhook information' },
      { status: 500 }
    );
  }
}

export async function POST(
  request: NextRequest,
  { params }: { params: { workflowId: string } }
) {
  try {
    const workflowId = params.workflowId;
    const body = await request.json();
    
    // Log the webhook execution
    const execution = {
      id: `webhook_${Date.now()}`,
      timestamp: new Date().toISOString(),
      source_ip: request.headers.get('x-forwarded-for') || 'unknown',
      user_agent: request.headers.get('user-agent') || 'unknown',
      payload: body,
      workflow_id: workflowId
    };
    
    if (!webhookExecutions[workflowId]) {
      webhookExecutions[workflowId] = [];
    }
    webhookExecutions[workflowId].push(execution);
    
    // Keep only last 100 executions per workflow
    if (webhookExecutions[workflowId].length > 100) {
      webhookExecutions[workflowId] = webhookExecutions[workflowId].slice(-100);
    }
    
    // Forward to LangFlow trigger API
    const triggerResponse = await fetch(`${request.nextUrl.origin}/api/trigger`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        workflowId: workflowId,
        engine: 'langflow',
        triggerType: 'webhook',
        inputPayload: body
      })
    });
    
    if (!triggerResponse.ok) {
      throw new Error(`Trigger API error: ${triggerResponse.status}`);
    }
    
    const triggerResult = await triggerResponse.json();
    
    return NextResponse.json({
      success: true,
      execution_id: execution.id,
      run_id: triggerResult.result?.run_id,
      message: 'Webhook received and workflow triggered',
      timestamp: execution.timestamp
    });
    
  } catch (error) {
    console.error('Error processing webhook:', error);
    return NextResponse.json(
      { 
        error: 'Failed to process webhook',
        details: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    );
  }
}

// Handle other HTTP methods
export async function PUT(
  request: NextRequest,
  { params }: { params: { workflowId: string } }
) {
  return POST(request, { params });
}

export async function PATCH(
  request: NextRequest,
  { params }: { params: { workflowId: string } }
) {
  return POST(request, { params });
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: { workflowId: string } }
) {
  try {
    const workflowId = params.workflowId;
    
    // Clear webhook execution history
    delete webhookExecutions[workflowId];
    
    return NextResponse.json({
      success: true,
      message: 'Webhook execution history cleared',
      workflow_id: workflowId
    });
  } catch (error) {
    console.error('Error clearing webhook history:', error);
    return NextResponse.json(
      { error: 'Failed to clear webhook history' },
      { status: 500 }
    );
  }
}

// Handle preflight requests for CORS
export async function OPTIONS() {
  return new Response(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, PATCH, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
      'Access-Control-Max-Age': '86400'
    }
  });
}
