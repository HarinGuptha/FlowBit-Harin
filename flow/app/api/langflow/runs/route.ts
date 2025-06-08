import { NextRequest, NextResponse } from 'next/server';

// Mock data for development - replace with actual LangFlow API calls
const mockRuns = [
  {
    id: 'run_001',
    flow_name: 'Email Agent',
    status: 'completed',
    duration: 2340,
    created_at: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
    input_data: { content: 'Angry customer email...' },
    output_data: { classification: 'complaint', escalation: true }
  },
  {
    id: 'run_002',
    flow_name: 'JSON Agent',
    status: 'completed',
    duration: 1890,
    created_at: new Date(Date.now() - 1000 * 60 * 15).toISOString(),
    input_data: { content: '{"suspicious": "data"}' },
    output_data: { anomaly_score: 0.95, risk_level: 'high' }
  },
  {
    id: 'run_003',
    flow_name: 'PDF Agent',
    status: 'running',
    duration: null,
    created_at: new Date(Date.now() - 1000 * 30).toISOString(),
    input_data: { content: 'High-value invoice document...' },
    output_data: null
  },
  {
    id: 'run_004',
    flow_name: 'Classifier Agent',
    status: 'failed',
    duration: 567,
    created_at: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
    input_data: { content: 'Invalid input data' },
    output_data: null,
    error: 'Invalid input format'
  }
];

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const limit = parseInt(searchParams.get('limit') || '50');
    
    // In production, this would call the actual LangFlow API
    const langflowUrl = process.env.LANGFLOW_BASE_URL || 'http://localhost:7860';
    
    // For now, return mock data
    const runs = mockRuns.slice(0, limit).map(run => ({
      id: run.id,
      flow_name: run.flow_name,
      status: run.status,
      duration: run.duration,
      created_at: run.created_at,
      input_preview: typeof run.input_data.content === 'string' 
        ? run.input_data.content.substring(0, 100) + '...'
        : JSON.stringify(run.input_data).substring(0, 100) + '...'
    }));

    return NextResponse.json({
      runs,
      total: mockRuns.length,
      limit
    });

  } catch (error) {
    console.error('Error fetching LangFlow runs:', error);
    return NextResponse.json(
      { error: 'Failed to fetch runs' },
      { status: 500 }
    );
  }
}

// POST endpoint to create a new run
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { flow_id, input_data, flow_name } = body;

    // In production, this would call the actual LangFlow API
    const langflowUrl = process.env.LANGFLOW_BASE_URL || 'http://localhost:7860';
    
    // Mock response for development
    const newRun = {
      id: `run_${Date.now()}`,
      flow_name: flow_name || 'Unknown Flow',
      status: 'running',
      duration: null,
      created_at: new Date().toISOString(),
      input_data,
      output_data: null
    };

    // Add to mock data (in production, this would be handled by LangFlow)
    mockRuns.unshift(newRun);

    // Simulate processing completion after a delay
    setTimeout(() => {
      const runIndex = mockRuns.findIndex(run => run.id === newRun.id);
      if (runIndex !== -1) {
        mockRuns[runIndex].status = 'completed';
        mockRuns[runIndex].duration = Math.floor(Math.random() * 3000) + 500;
        mockRuns[runIndex].output_data = {
          result: 'Processing completed successfully',
          confidence: 0.85 + Math.random() * 0.15
        };
      }
    }, 2000 + Math.random() * 3000);

    return NextResponse.json({
      run_id: newRun.id,
      status: 'started',
      message: 'Run initiated successfully'
    });

  } catch (error) {
    console.error('Error creating LangFlow run:', error);
    return NextResponse.json(
      { error: 'Failed to create run' },
      { status: 500 }
    );
  }
}
