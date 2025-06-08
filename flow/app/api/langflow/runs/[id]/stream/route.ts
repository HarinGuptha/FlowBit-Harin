import { NextRequest, NextResponse } from 'next/server';

// Mock streaming data for development
const mockStreamData: Record<string, any[]> = {
  'run_001': [
    { timestamp: Date.now() - 5000, level: 'info', message: 'Starting email processing workflow', node_id: 'input-1' },
    { timestamp: Date.now() - 4500, level: 'info', message: 'Email content received and validated', node_id: 'input-1' },
    { timestamp: Date.now() - 4000, level: 'info', message: 'Parsing email structure...', node_id: 'parser-1' },
    { timestamp: Date.now() - 3500, level: 'info', message: 'Email parsed successfully', node_id: 'parser-1' },
    { timestamp: Date.now() - 3000, level: 'info', message: 'Analyzing tone and sentiment...', node_id: 'analyzer-1' },
    { timestamp: Date.now() - 2500, level: 'warning', message: 'Angry tone detected - escalation may be required', node_id: 'analyzer-1' },
    { timestamp: Date.now() - 2000, level: 'info', message: 'Sentiment analysis complete', node_id: 'analyzer-1' },
    { timestamp: Date.now() - 1500, level: 'info', message: 'Combining analysis results...', node_id: 'output-1' },
    { timestamp: Date.now() - 1000, level: 'success', message: 'Email processing completed successfully', node_id: 'output-1' }
  ],
  'run_002': [
    { timestamp: Date.now() - 4000, level: 'info', message: 'Starting JSON validation and analysis', node_id: 'input-1' },
    { timestamp: Date.now() - 3500, level: 'info', message: 'JSON syntax validation passed', node_id: 'validator-1' },
    { timestamp: Date.now() - 3000, level: 'info', message: 'Running anomaly detection algorithms...', node_id: 'anomaly-detector-1' },
    { timestamp: Date.now() - 2500, level: 'error', message: 'CRITICAL: Extremely high amount detected', node_id: 'anomaly-detector-1' },
    { timestamp: Date.now() - 2000, level: 'warning', message: 'Anomaly score: 0.95 - flagging for review', node_id: 'anomaly-detector-1' },
    { timestamp: Date.now() - 1500, level: 'success', message: 'JSON analysis completed', node_id: 'output-1' }
  ]
};

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  const runId = params.id;
  
  // Create a readable stream for Server-Sent Events
  const stream = new ReadableStream({
    start(controller) {
      // Set up SSE headers
      const encoder = new TextEncoder();
      
      // Send initial connection message
      controller.enqueue(
        encoder.encode(`data: ${JSON.stringify({ 
          type: 'connection', 
          message: 'Connected to run stream',
          run_id: runId 
        })}\n\n`)
      );

      // Get mock data for this run
      const streamData = mockStreamData[runId] || [];
      let messageIndex = 0;

      // Function to send the next message
      const sendNextMessage = () => {
        if (messageIndex < streamData.length) {
          const message = streamData[messageIndex];
          const sseData = {
            type: 'log',
            data: {
              timestamp: new Date(message.timestamp).toISOString(),
              level: message.level,
              message: message.message,
              node_id: message.node_id,
              run_id: runId
            }
          };
          
          controller.enqueue(
            encoder.encode(`data: ${JSON.stringify(sseData)}\n\n`)
          );
          
          messageIndex++;
          
          // Schedule next message with realistic delay
          setTimeout(sendNextMessage, 500 + Math.random() * 1000);
        } else {
          // Send completion message
          controller.enqueue(
            encoder.encode(`data: ${JSON.stringify({ 
              type: 'complete', 
              message: 'Stream completed',
              run_id: runId 
            })}\n\n`)
          );
          
          // Close the stream after a short delay
          setTimeout(() => {
            controller.close();
          }, 1000);
        }
      };

      // Start sending messages after a short delay
      setTimeout(sendNextMessage, 1000);
    },
    
    cancel() {
      console.log('Stream cancelled for run:', runId);
    }
  });

  // Return the stream with appropriate headers for SSE
  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET',
      'Access-Control-Allow-Headers': 'Cache-Control'
    }
  });
}

// Handle preflight requests for CORS
export async function OPTIONS() {
  return new Response(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET',
      'Access-Control-Allow-Headers': 'Cache-Control'
    }
  });
}
